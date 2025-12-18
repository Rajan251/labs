# Performance Tuning: A Scientific Approach

**Level:** Expert / Performance Engineer
**Focus:** Methodical optimization based on measurement, not guesswork.

---

## 1. Performance Analysis Methodology

### 1.1 The Scientific Method
1.  **Define Baseline**: Measure current performance under normal load. Record metrics (latency p50/p95/p99, throughput, CPU%, etc.).
2.  **Identify Bottleneck**: Use the USE Method (below).
3.  **Form Hypothesis**: "I believe X is the bottleneck because Y".
4.  **Test**: Change **ONE** variable. Never tune multiple things simultaneously.
5.  **Measure Impact**: Compare before/after. Did it improve? By how much?
6.  **Document**: Keep a tuning journal. What changed, why, and the result.

### 1.2 USE Method (Brendan Gregg)
For every resource (CPU, Memory, Disk, Network), check:
*   **Utilization**: % busy time. (e.g., `mpstat` for CPU).
*   **Saturation**: Queue depth or waiting. (e.g., Load Average for CPU runqueue).
*   **Errors**: Hardware/software errors. (e.g., `dmesg`, NIC drops).

---

## 2. CPU Performance Factors

### 2.1 Frequency Scaling Governors
*   **performance**: Lock CPU at max frequency. **Use for latency-sensitive apps** (Trading, Gaming).
*   **powersave**: Dynamic scaling. Good for laptops, bad for servers.
*   **ondemand**: Legacy dynamic. Replaced by `schedutil` in modern kernels.
*   **Command**: `cpupower frequency-set -g performance`.

### 2.2 Hyper-Threading (SMT)
*   **Benefit**: Two logical cores per physical core. Good for **I/O-bound** workloads (web servers waiting on disk/network).
*   **Drawback**: Shared L1/L2 cache. **Bad for CPU-bound** (scientific computing). Can cause 10-20% slowdown.
*   **Disable**: BIOS or `echo off > /sys/devices/system/cpu/smt/control`.

### 2.3 NUMA (Non-Uniform Memory Access)
Multi-socket servers have local and remote memory.
*   **Problem**: Process on Socket 0 accessing RAM on Socket 1 = 2x latency.
*   **Solution**: `numactl --cpunodebind=0 --membind=0 ./app` (Bind process to socket 0 CPU and RAM).

---

## 3. Memory Optimization

### 3.1 Swappiness
Controls tendency to swap vs reclaim page cache.
*   **Value 0**: Avoid swap at all costs (Databases).
*   **Value 60**: Default. Balanced.
*   **Value 100**: Aggressive swapping (Rarely useful).
*   **Command**: `sysctl vm.swappiness=10`.

### 3.2 Transparent Hugepages (THP)
*   **Standard**: 4KB pages. Managing 100GB = 25 million page table entries.
*   **Hugepages**: 2MB pages. Reduces TLB misses.
*   **Good For**: Databases (Oracle, Postgres), Java Heap.
*   **Bad For**: Redis, Memcached (causes latency spikes during compaction).
*   **Disable**: `echo never > /sys/kernel/mm/transparent_hugepage/enabled`.

### 3.3 Working Set Size
The amount of RAM your app actively uses.
*   **Measure**: `perf stat -e cache-misses,cache-references ./app`.
*   **Goal**: Working set < RAM. If not, add RAM or reduce dataset.

---

## 4. Storage Performance

### 4.1 Read-Ahead
Kernel pre-fetches sequential blocks.
*   **Default**: 128 sectors (64KB).
*   **Streaming**: Increase to 8192 (4MB). `blockdev --setra 8192 /dev/sda`.
*   **Random I/O**: Decrease to 0 (Databases doing their own prefetch).

### 4.2 Filesystem Block Size
*   **Small Files** (Mail, Logs): 1KB or 2KB blocks (less waste).
*   **Large Files** (Video, Backups): 64KB blocks (fewer metadata ops).
*   **Set at mkfs**: `mkfs.xfs -b size=4096`.

### 4.3 Write Barriers
Ensures data hits persistent media before returning success.
*   **Enabled** (`barrier=1`): Safe. Slow.
*   **Disabled** (`barrier=0`): Fast. **Data loss risk** on power failure.
*   **Use Case**: Disable only if you have Battery-Backed Cache (RAID controller) or can tolerate loss.

---

## 5. Network Optimization

### 5.1 TCP Buffer Auto-Tuning
*   **Enabled by default**: `net.ipv4.tcp_moderate_rcvbuf=1`.
*   Kernel dynamically adjusts `SO_RCVBUF` based on RTT and bandwidth.
*   **Manual Override**: Only if you know better than the kernel (rare).

### 5.2 Interrupt Coalescing
NIC batches interrupts to reduce CPU overhead.
*   **High Latency**: Disable (`ethtool -C eth0 rx-usecs 0`).
*   **High Throughput**: Increase (`rx-usecs 100`).

### 5.3 Congestion Control
*   **cubic**: Default. Good general purpose.
*   **bbr**: Google's algorithm. **Best for high-latency links** (Satellite, Intercontinental).
*   **Command**: `sysctl net.ipv4.tcp_congestion_control=bbr`.

---

## 6. Application-Specific Tuning

### 6.1 Web Servers (Nginx)
*   **worker_processes**: Set to CPU core count.
*   **worker_connections**: 1024 (default) to 10000+ (high traffic).
*   **keepalive_timeout**: 65s (default) to 5s (reduce TIME_WAIT).

### 6.2 Databases (MySQL/Postgres)
*   **Filesystem**: XFS with `noatime`.
*   **I/O**: Use `O_DIRECT` (bypass page cache).
*   **Buffer Pool**: 70-80% of RAM.
*   **Log Files**: Place on separate, fast disk (SSD).

### 6.3 Java Applications
*   **Heap Size**: `-Xms` = `-Xmx` (Avoid dynamic resizing).
*   **GC**: G1GC (default, balanced) vs ZGC (ultra-low pause).
*   **NUMA**: `-XX:+UseNUMA`.

---

## 7. Decision Trees

### 7.1 Latency-Sensitive (Trading, Gaming)
1.  CPU Governor: `performance`.
2.  Disable HT if CPU-bound.
3.  Pin to cores: `taskset`.
4.  Scheduler: `mq-deadline` or `none` (NVMe).
5.  Network: Disable interrupt coalescing.

### 7.2 Throughput-Oriented (Batch Processing)
1.  Enable batching everywhere (TCP Nagle, disk write-back).
2.  Large buffers (`net.core.rmem_max`, `vm.dirty_ratio`).
3.  Scheduler: `none` (NVMe).
4.  Read-ahead: High (`8192`).

### 7.3 Virtualized/Containerized
1.  **CPU Pinning**: Avoid vCPU migration (`cset shield`).
2.  **Hugepages**: Pre-allocate for VMs.
3.  **I/O**: Use virtio-scsi (not IDE emulation).
4.  **Network**: SR-IOV for near-native performance.

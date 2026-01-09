# Advanced Linux Kernel Architecture

**Level:** Expert / Kernel Developer / Performance Engineer  
**Focus:** Deep kernel internals, performance optimization, and troubleshooting

---

## 1. KERNEL SPACE VS USER SPACE

### 1.1 Ring Levels and Protection
```
Ring 0 (Kernel Mode)    : Full hardware access, privileged instructions
Ring 3 (User Mode)      : Restricted access, must use syscalls
```

### 1.2 System Call Path
```
User Application (glibc)
    ↓ (wrapper function)
syscall instruction
    ↓ (CPU mode switch)
Kernel syscall handler
    ↓ (dispatch table)
Specific syscall implementation
    ↓ (return)
User space (result in register)
```

**Cost of Context Switch**:
```bash
# Measure syscall overhead
perf stat -e context-switches,cpu-clock ./program

# Typical cost: 1-5 microseconds per switch
```

### 1.3 Kernel Bypass Techniques
- **DPDK**: Bypass kernel networking stack (userspace drivers)
- **SPDK**: Bypass kernel storage stack (NVMe userspace drivers)
- **io_uring**: Minimize syscalls with shared ring buffers

---

## 2. MEMORY MANAGEMENT ADVANCED

### 2.1 Virtual Memory Architecture
```
Virtual Address → Page Table Walk → Physical Address
                     ↓ (cached in)
                    TLB (fast)
```

**Page Table Levels** (x86_64):
```
PGD → PUD → PMD → PTE → Physical Page
```

### 2.2 Hugepages
```bash
# 2MB hugepages (default)
echo 1024 > /proc/sys/vm/nr_hugepages

# 1GB hugepages (requires boot parameter)
# hugepagesz=1G hugepages=4

# Check usage
cat /proc/meminfo | grep -i huge
```

**Trade-offs**:
- **2MB pages**: Reduce TLB misses, good for databases
- **1GB pages**: Extreme TLB reduction, but inflexible

### 2.3 NUMA Architecture
```bash
# Show NUMA topology
numactl --hardware

# Bind process to node 0
numactl --cpunodebind=0 --membind=0 ./app

# Check NUMA stats
numastat

# Auto NUMA balancing
cat /proc/sys/kernel/numa_balancing  # 1 = enabled
```

**Cross-node penalty**: 1.5-3x slower than local access

### 2.4 OOM Killer
```bash
# OOM score (higher = more likely to be killed)
cat /proc/<PID>/oom_score

# Adjust OOM score
echo -1000 > /proc/<PID>/oom_score_adj  # Never kill
echo 1000 > /proc/<PID>/oom_score_adj   # Kill first
```

---

## 3. PROCESS SCHEDULER INTERNALS

### 3.1 CFS (Completely Fair Scheduler)
**Virtual Runtime (vruntime)**:
```
vruntime = physical_runtime * (NICE_0_LOAD / task_weight)
```

**Scheduler Tunables**:
```bash
# Latency target (default: 6ms)
cat /proc/sys/kernel/sched_latency_ns

# Minimum granularity (default: 0.75ms)
cat /proc/sys/kernel/sched_min_granularity_ns

# Wakeup granularity (default: 1ms)
cat /proc/sys/kernel/sched_wakeup_granularity_ns
```

### 3.2 Real-Time Scheduling
```bash
# Set real-time priority
chrt -f 99 ./critical_app  # SCHED_FIFO, priority 99
chrt -r 50 ./app           # SCHED_RR, priority 50

# Check RT throttling
cat /proc/sys/kernel/sched_rt_runtime_us  # 950000 (95%)
cat /proc/sys/kernel/sched_rt_period_us   # 1000000 (1s)
```

---

## 4. I/O SUBSYSTEM ARCHITECTURE

### 4.1 Block Layer Stack
```
Application
    ↓
VFS (Virtual Filesystem)
    ↓
Page Cache
    ↓
Block Layer (blk-mq)
    ↓
I/O Scheduler (mq-deadline, bfq, kyber)
    ↓
Device Driver
    ↓
Hardware
```

### 4.2 I/O Schedulers
```bash
# Check current scheduler
cat /sys/block/sda/queue/scheduler
# Output: [mq-deadline] kyber bfq none

# Change scheduler
echo bfq > /sys/block/sda/queue/scheduler

# Scheduler comparison:
# mq-deadline: General purpose, low latency
# bfq: Budget Fair Queueing, interactive workloads
# kyber: Token-based, low latency
# none: No scheduling (NVMe, fast devices)
```

### 4.3 Direct vs Buffered I/O
```c
// Buffered I/O (uses page cache)
fd = open("file", O_RDWR);

// Direct I/O (bypass page cache)
fd = open("file", O_RDWR | O_DIRECT);

// Synchronous I/O (wait for disk)
fd = open("file", O_RDWR | O_SYNC);
```

---

## 5. NETWORKING STACK INTERNALS

### 5.1 TCP/IP Stack Flow
```
Application
    ↓ (socket API)
Socket Layer
    ↓
TCP/UDP Layer (sk_buff allocation)
    ↓
IP Layer (routing)
    ↓
Netfilter (iptables hooks)
    ↓
Device Driver (NAPI)
    ↓
Hardware NIC
```

### 5.2 Network Performance Features
```bash
# RSS (Receive Side Scaling) - hardware
ethtool -l eth0

# RPS (Receive Packet Steering) - software
echo "ff" > /sys/class/net/eth0/queues/rx-0/rps_cpus

# XDP (eXpress Data Path)
ip link set dev eth0 xdp obj xdp_prog.o
```

---

## 6. INTER-PROCESS COMMUNICATION

### 6.1 Shared Memory
```bash
# System V shared memory
ipcs -m

# POSIX shared memory
ls -l /dev/shm/

# Performance: Fastest IPC (no kernel involvement after setup)
```

### 6.2 Message Passing
```bash
# Unix domain sockets (fastest socket type)
# Named pipes (FIFO)
mkfifo /tmp/mypipe

# Netlink (kernel-user communication)
# Used by: ip, tc, ethtool
```

---

## 7. KERNEL MODULES

### 7.1 Module Management
```bash
# List loaded modules
lsmod

# Load module
modprobe module_name

# Unload module
modprobe -r module_name

# Module info
modinfo module_name

# Module dependencies
depmod -a
```

### 7.2 Kernel Debugging
```bash
# Enable ftrace
echo function > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on
cat /sys/kernel/debug/tracing/trace

# kprobes (dynamic tracing)
echo 'p:myprobe do_sys_open filename=+0(%si):string' > \
    /sys/kernel/debug/tracing/kprobe_events

# perf events
perf record -e sched:sched_switch -a sleep 10
perf report
```

---

## 8. VIRTUALIZATION SUPPORT

### 8.1 KVM Architecture
```bash
# Check KVM support
lsmod | grep kvm
cat /proc/cpuinfo | grep -E 'vmx|svm'

# KVM modules
# kvm.ko        - Core KVM
# kvm_intel.ko  - Intel VT-x
# kvm_amd.ko    - AMD-V
```

### 8.2 Container Primitives
```bash
# Namespaces
lsns  # List namespaces

# Cgroups v2
mount | grep cgroup2
cat /sys/fs/cgroup/cgroup.controllers

# User namespace mapping
cat /proc/<PID>/uid_map
cat /proc/<PID>/gid_map
```

---

## 9. SECURITY SUBSYSTEMS

### 9.1 LSM (Linux Security Modules)
```bash
# Check active LSM
cat /sys/kernel/security/lsm
# Output: lockdown,capability,yama,apparmor

# SELinux
getenforce
setenforce 0  # Permissive

# AppArmor
aa-status
```

---

## 10. PERFORMANCE ANALYSIS

### 10.1 perf Subsystem
```bash
# CPU profiling
perf record -F 99 -a -g -- sleep 30
perf report

# Hardware counters
perf stat -e cycles,instructions,cache-misses ./app

# Flame graph
perf record -F 99 -a -g -- sleep 30
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

### 10.2 eBPF
```bash
# Trace TCP connections
bpftrace -e 'kprobe:tcp_connect { printf("%s\n", comm); }'

# Count syscalls by process
bpftrace -e 'tracepoint:raw_syscalls:sys_enter { @[comm] = count(); }'
```

---

## 11. EMERGING FEATURES

### 11.1 io_uring
```c
// Asynchronous I/O with io_uring
struct io_uring ring;
io_uring_queue_init(QUEUE_DEPTH, &ring, 0);

// Submit read operation
struct io_uring_sqe *sqe = io_uring_get_sqe(&ring);
io_uring_prep_read(sqe, fd, buf, size, offset);
io_uring_submit(&ring);

// Wait for completion
struct io_uring_cqe *cqe;
io_uring_wait_cqe(&ring, &cqe);
```

**Benefits**: 10-20% better performance than traditional async I/O

---

## 12. PRACTICAL EXAMPLES

### 12.1 Trace Syscall Path
```bash
# Trace open() syscall
echo 'p:myprobe do_sys_open' > /sys/kernel/debug/tracing/kprobe_events
echo 1 > /sys/kernel/debug/tracing/events/kprobes/myprobe/enable
cat /sys/kernel/debug/tracing/trace
```

### 12.2 Memory Leak Detection
```bash
# Enable kmemleak
echo scan > /sys/kernel/debug/kmemleak
cat /sys/kernel/debug/kmemleak
```

### 12.3 I/O Path Analysis
```bash
# Trace block I/O
blktrace -d /dev/sda -o trace
blkparse trace

# Analyze queue depths
cat /sys/block/sda/queue/nr_requests
```

---

## 13. TROUBLESHOOTING KERNEL ISSUES

### 13.1 Kernel Panic Analysis
```bash
# Analyze crash dump
crash /usr/lib/debug/vmlinux /var/crash/vmcore

# Common commands in crash:
bt        # Backtrace
log       # Kernel log
ps        # Process list
```

### 13.2 Lockdep Reports
```bash
# Enable lockdep
echo 1 > /proc/sys/kernel/lock_stat

# Check for deadlocks
cat /proc/lockdep_stats
```

---

## 14. PRODUCTION TUNING

### 14.1 Critical Kernel Parameters
```bash
# Network
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048

# Memory
vm.swappiness = 10
vm.dirty_ratio = 10

# Scheduler
kernel.sched_migration_cost_ns = 500000
```

### 14.2 Live Kernel Patching
```bash
# kpatch (Red Hat)
kpatch load patch.ko

# Check loaded patches
kpatch list
```

---

## 15. QUICK REFERENCE

### Kernel Debugging Commands
```bash
dmesg -T                    # Kernel ring buffer
cat /proc/slabinfo          # Kernel object caches
cat /proc/buddyinfo         # Memory fragmentation
cat /proc/vmstat            # VM statistics
cat /proc/interrupts        # Interrupt counts
cat /proc/softirqs          # SoftIRQ statistics
```

### Performance Monitoring
```bash
perf top                    # Real-time profiling
perf stat -a sleep 10       # System-wide stats
bpftrace -l                 # List tracepoints
```

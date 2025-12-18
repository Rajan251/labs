# Linux Storage Architecture Deep Dive

**Level:** Expert / Storage Engineer
**Focus:** Block Layer, Filesystems, LVM, and Performance Tuning.

---

## 1. Block Layer Architecture

The Block Layer sits between the Filesystem and the Device Driver.

### 1.1 Request Queue Management
*   **Single Queue (Legacy)**: Single lock for the queue. bottleneck on high-IOPS SSDs.
*   **Multi-Queue (`blk-mq`)**:
    *   **Architecture**: Per-CPU Software Queues map to Hardware Submission Queues.
    *   **Benefit**: Eliminates lock contention. Essential for NVMe which supports 64k queues.
    *   **Status**: Default in modern kernels (RHEL 8+).

### 1.2 IO Schedulers
The scheduler decides order of requests to optimize head movement (HDD) or latency (SSD).
*   **mq-deadline**: Group reads vs writes. Enforce deadlines. **Best for Databases** and Server workloads.
*   **bfq** (Budget Fair Queueing): Complex heuristics. Great for **Desktop/Interactive** systems (prevents mouse lag during heavy copying). High CPU overhead.
*   **none**: **Mandatory for NVMe**. NVMe drives have internal logic better than the OS. Don't waste CPU cycles reordering.
    *   *Check*: `cat /sys/block/sda/queue/scheduler`.

---

## 2. Filesystem Comparison Matrix

| Feature | **Ext4** | **XFS** | **Btrfs** | **ZFS** |
| :--- | :--- | :--- | :--- | :--- |
| **Type** | Journaling | Journaling (Parallel) | CoW (Copy on Write) | CoW + Volume Manager |
| **Stability** | Rock Solid | Enterprise Standard | Improving (RAID5/6 risky) | Rock Solid |
| **Scalability** | Good (upto 1EB) | Excellent (Petabytes) | Good | Excellent |
| **Best Use** | Boot keys, General VM | Databases, Big Data | Workstation, Containers | NAS, Enterprise Storage |
| **Shrink?** | Yes (Offline) | **No** | Yes | No (Vdev removal limited) |
| **Key Feat.** | Backward compat | Parallel I/O | Snapshots, Compression | ARC Cache, Dedup, Integrity |

---

## 3. LVM Deep Dive

Logical Volume Manager abstracts physical disks.

### 3.1 Mapping Architecture
*   **PV (Physical Volume)**: The disk (`/dev/sdb`).
*   **VG (Volume Group)**: Pool of storage.
*   **PE (Physical Extent)**: The smallest chunk (default 4MB).
*   **LV (Logical Volume)**: Made of LEs (Logical Extents). LVM maps LE -> PE.
    *   **Linear**: LE 1-100 -> PE 1-100 on PV1.
    *   **Striped**: LE 1 -> PV1, LE 2 -> PV2. (Higher Performance).

### 3.2 Advanced Features
*   **Thin Provisioning**: Allocate 10TB LV on 1TB Disk.
    *   *Risk*: If pool fills up, file systems crash (mount read-only). Monitor CLOSELY using `lvs` thresholds.
*   **Snapshots**:
    *   **Thick (Old)**: Copy-on-Write penalty. Writing to origin requires copying old block to snapshot volume. Degrades performance.
    *   **Thin (New)**: No copy penalty. Just a metadata pointer update.
*   **pvmove**: Live data migration.
    *   `pvmove /dev/sdb /dev/sdc`. Moves PEs while system is running.
    *   *Risk*: High I/O impact.

---

## 4. Direct vs Buffered I/O

### 4.1 Buffered I/O (Default)
`write()` -> Kernel Page Cache (RAM) -> Disk (later).
*   **Pros**: Fast response to app. Read-ahead caching.
*   **Cons**: Memory pressure (Double caching if DB has its own buffer). Data loss on power cut (unless `fsync`).

### 4.2 Direct I/O (`O_DIRECT`)
`write()` -> Disk.
*   **Bypasses**: Page Cache.
*   **Use Case**: **Databases** (Oracle, MySQL, Postgres). They manage their own caching (Buffer Pool / Shared Global Area) better than the generic OS.

### 4.3 Async I/O (AIO) vs io_uring
*   **AIO**: Old. Only worked well with O_DIRECT. Blocking in many edge cases.
*   **io_uring**: New (Kernel 5.1+). Submission/Completion Ring buffers. Zero-copy.
    *   **Performance**: Massive IOPS increase for NVMe. Used by modern DBs.

### 4.4 Tuning Cache
*   `vm.vfs_cache_pressure`: Control tendency to reclaim Inode/Dentry memory vs Page Cache.
    *   Default: 100.
    *   Value >100: Reclaim inodes faster (Good for servers with millions of small files/mail).

---

## 5. RAID Considerations

### 5.1 Software RAID (`mdadm`)
*   **Levels**: 0 (Striping), 1 (Mirror), 5 (Parity), 6 (Double Parity), 10 (Stripe of Mirrors).
*   **Write Hole**: On RAID 5/6, if power fails during a write (Data written, Parity undefined), the array is corrupt.
    *   *Fix*: Hardware RAID with Battery (BBU) or ZFS (Transaction Groups).

### 5.2 RAID vs LVM
*   **LVM Mirroring**: Flexible but CPU heavy.
*   **MDADM**: Faster/Simpler for pure RAID.
*   **Recommendation**: Use MDADM for redundancy, LVM on top for volume management.

---

## 6. Performance Optimization Patterns

### 6.1 Database Workloads (Random R/W)
*   **FS**: XFS.
*   **Device**: NVMe or SSD RAID 10.
*   **Scheduler**: `none` (NVMe) or `mq-deadline` (SATA).
*   **Mount**: `noatime`.
*   **App**: use `O_DIRECT`.

### 6.2 Streaming / Media (Sequential Read)
*   **FS**: XFS (handle large files well).
*   **RAID**: RAID 6 (Capacity + Redundancy).
*   **Read Ahead**: Increase aggressively. `blockdev --setra 4096 /dev/db_disk`.
*   **Stripe Alignment**: Make FS stripe width match RAID stripe width (`mkfs.xfs -d su=64k,sw=4`).

### 6.3 VM Storage (Images)
*   **Format**: Raw (fastest active) or Qcow2 (features).
*   **Host FS**: File-based images on XFS (fragmentation resistance).
*   **LVM**: Block-based (LVM Logical Volume passed directly to VM) is fastest (no FS overhead).

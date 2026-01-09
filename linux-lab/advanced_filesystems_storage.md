# Advanced Filesystems & Storage Architecture

**Level:** Expert / Storage Engineer / Performance Architect  
**Focus:** Filesystem internals, storage optimization, and advanced features

---

## 1. VIRTUAL FILESYSTEM SWITCH (VFS)

### 1.1 VFS Objects
```
Application
    ↓
VFS Layer
    ├─ superblock    : Filesystem metadata
    ├─ inode         : File metadata (permissions, timestamps)
    ├─ dentry        : Directory entry (name → inode mapping)
    └─ file          : Open file descriptor
    ↓
Specific Filesystem (ext4, xfs, btrfs)
```

### 1.2 Caches
```bash
# Dentry cache (dcache)
cat /proc/slabinfo | grep dentry

# Inode cache
cat /proc/slabinfo | grep inode

# Drop caches (testing only!)
echo 3 > /proc/sys/vm/drop_caches
```

---

## 2. FILESYSTEM COMPARISON

### 2.1 Ext4 Deep Dive

**On-Disk Structure**:
```
Superblock → Group Descriptors → Inode Table → Data Blocks
```

**Journaling Modes**:
```bash
# journal: Safest, slowest (metadata + data)
mount -o data=journal /dev/sda1 /mnt

# ordered: Default (metadata journaled, data ordered)
mount -o data=ordered /dev/sda1 /mnt

# writeback: Fastest, least safe (metadata only)
mount -o data=writeback /dev/sda1 /mnt
```

**Extents vs Indirect Blocks**:
- **Extents**: Contiguous blocks (efficient for large files)
- **Indirect**: Block pointers (legacy, fragmentation-prone)

**Delayed Allocation**:
```bash
# Check delayed allocation
tune2fs -l /dev/sda1 | grep delalloc

# Disable (not recommended)
mount -o nodelalloc /dev/sda1 /mnt
```

### 2.2 XFS Architecture

**Key Features**:
- **Allocation Groups**: Parallel I/O operations
- **B+trees**: Efficient metadata management
- **Delayed Logging**: Better performance

```bash
# Create XFS with specific AG size
mkfs.xfs -d agcount=16 /dev/sda1

# Online defragmentation
xfs_fsr /mnt/xfs

# Online growing
xfs_growfs /mnt/xfs

# Check fragmentation
xfs_db -r -c frag /dev/sda1
```

### 2.3 Btrfs Advanced Features

**Copy-on-Write (CoW)**:
```bash
# Create subvolume
btrfs subvolume create /mnt/btrfs/subvol

# Snapshot (instant, CoW)
btrfs subvolume snapshot /mnt/btrfs/subvol /mnt/btrfs/snap

# Send/receive (incremental backup)
btrfs send /mnt/btrfs/snap | btrfs receive /backup/
```

**RAID Support**:
```bash
# RAID1 (2 copies)
mkfs.btrfs -d raid1 -m raid1 /dev/sda /dev/sdb

# RAID10
mkfs.btrfs -d raid10 -m raid10 /dev/sd{a,b,c,d}

# Check RAID status
btrfs filesystem show
```

**Checksums & Self-Healing**:
```bash
# Scrub filesystem (verify checksums)
btrfs scrub start /mnt/btrfs
btrfs scrub status /mnt/btrfs
```

### 2.4 ZFS on Linux

**ARC (Adaptive Replacement Cache)**:
```bash
# Check ARC stats
cat /proc/spl/kstat/zfs/arcstats

# Limit ARC size (in /etc/modprobe.d/zfs.conf)
options zfs zfs_arc_max=8589934592  # 8GB
```

**Dataset Hierarchy**:
```bash
# Create pool
zpool create tank /dev/sda

# Create datasets
zfs create tank/data
zfs create tank/data/mysql

# Set properties (inherited)
zfs set compression=lz4 tank/data
zfs set recordsize=16k tank/data/mysql
```

**Deduplication**:
```bash
# Enable dedup (RAM intensive!)
zfs set dedup=on tank/data

# Check dedup ratio
zpool list -o name,dedupratio
```

---

## 3. STORAGE STACK OPTIMIZATION

### 3.1 I/O Alignment
```bash
# Check filesystem block size
tune2fs -l /dev/sda1 | grep "Block size"

# Check RAID stripe size
mdadm --detail /dev/md0 | grep "Chunk Size"

# Align filesystem to RAID stripe
# stripe_size = chunk_size * (num_disks - parity_disks)
mkfs.ext4 -E stride=16,stripe-width=64 /dev/md0
```

### 3.2 Read-Ahead Tuning
```bash
# Check current read-ahead
blockdev --getra /dev/sda

# Set read-ahead (KB)
blockdev --setra 8192 /dev/sda  # 8MB

# For sequential workloads: Increase
# For random workloads: Decrease
```

### 3.3 Caching Strategies
```bash
# Page cache stats
cat /proc/meminfo | grep -E 'Cached|Buffers'

# Control cache with vmtouch
vmtouch -t /path/to/file  # Load into cache
vmtouch -e /path/to/file  # Evict from cache
vmtouch -l /path/to/file  # Lock in cache
```

---

## 4. MOUNT OPTIONS DEEP DIVE

### 4.1 Performance Options
```bash
# noatime: Don't update access time (faster)
mount -o noatime /dev/sda1 /mnt

# nodiratime: Don't update directory access time
mount -o nodiratime /dev/sda1 /mnt

# relatime: Update atime only if older than mtime (default)
mount -o relatime /dev/sda1 /mnt

# discard: TRIM for SSDs
mount -o discard /dev/sda1 /mnt
```

### 4.2 Ext4 Specific
```bash
# Disable journaling (faster, risky)
tune2fs -O ^has_journal /dev/sda1

# Commit interval (default: 5s)
mount -o commit=30 /dev/sda1 /mnt

# Barrier control
mount -o barrier=0 /dev/sda1 /mnt  # Disable (UPS required!)
```

### 4.3 XFS Specific
```bash
# Log buffer size
mount -o logbsize=256k /dev/sda1 /mnt

# Allocation size
mount -o allocsize=64m /dev/sda1 /mnt

# No barriers (UPS required!)
mount -o nobarrier /dev/sda1 /mnt
```

---

## 5. ADVANCED FEATURES

### 5.1 FUSE (Filesystem in Userspace)
```bash
# SSHFS (remote filesystem over SSH)
sshfs user@remote:/path /mnt/remote

# EncFS (encrypted filesystem)
encfs ~/.encrypted ~/decrypted

# MergerFS (pool multiple disks)
mergerfs /mnt/disk1:/mnt/disk2 /mnt/pool
```

**Performance**: 20-30% slower than kernel filesystems

### 5.2 LVM Snapshots
```bash
# Create snapshot (10GB)
lvcreate -L 10G -s -n snap /dev/vg0/lv0

# Mount snapshot
mount /dev/vg0/snap /mnt/snap

# Merge snapshot back
lvconvert --merge /dev/vg0/snap
```

---

## 6. FILESYSTEM BENCHMARKING

### 6.1 fio (Flexible I/O Tester)
```bash
# Random read test
fio --name=randread --ioengine=libaio --iodepth=16 \
    --rw=randread --bs=4k --direct=1 --size=1G --numjobs=4

# Sequential write test
fio --name=seqwrite --ioengine=libaio --iodepth=1 \
    --rw=write --bs=1m --direct=1 --size=10G
```

### 6.2 Filesystem-Specific Tools
```bash
# Ext4 fragmentation
e4defrag -c /mnt/ext4

# XFS fragmentation
xfs_db -r -c frag /dev/sda1

# Btrfs balance (defrag)
btrfs balance start /mnt/btrfs
```

---

## 7. TROUBLESHOOTING

### 7.1 Filesystem Corruption
```bash
# Ext4 check (unmounted!)
e2fsck -f /dev/sda1

# XFS repair
xfs_repair /dev/sda1

# Btrfs check
btrfs check /dev/sda1
```

### 7.2 Performance Issues
```bash
# I/O statistics
iostat -x 1

# Per-process I/O
iotop

# Filesystem stats
cat /proc/fs/ext4/sda1/mb_groups
```

---

## 8. PRODUCTION RECOMMENDATIONS

### 8.1 Filesystem Selection
| Workload | Recommended FS | Reason |
|----------|---------------|--------|
| **Database** | XFS or ext4 | Stable, good performance |
| **VM Images** | XFS | Large files, parallel I/O |
| **Home Dirs** | ext4 | Mature, reliable |
| **Backup** | Btrfs or ZFS | Snapshots, compression |
| **Archive** | ZFS | Dedup, compression |

### 8.2 Mount Options by Workload
```bash
# Database (MySQL/PostgreSQL)
mount -o noatime,nodiratime,nobarrier /dev/sda1 /var/lib/mysql

# Web server
mount -o noatime,nodiratime /dev/sda1 /var/www

# General purpose
mount -o relatime /dev/sda1 /mnt
```

---

## 9. QUICK REFERENCE

### Common Commands
```bash
# Filesystem info
df -hT                    # Disk usage by type
findmnt                   # Mount tree
lsblk -f                  # Block devices with FS

# Inode usage
df -i

# Filesystem UUID
blkid /dev/sda1

# Tune filesystem
tune2fs -l /dev/sda1      # Ext4
xfs_info /mnt/xfs         # XFS
btrfs filesystem show     # Btrfs
```

### Performance Tuning
```bash
# Disable access time updates
mount -o noatime,nodiratime

# Increase commit interval
mount -o commit=60

# Enable TRIM for SSD
mount -o discard

# Increase read-ahead
blockdev --setra 8192 /dev/sda
```

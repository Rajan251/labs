# Linux System Architecture for Production Environments

**Level:** Expert / Senior Administrator
**Scope:** Boot, Kernel, Memory, Storage layers
**Goal:** Deep understanding of subsystems for performance tuning and troubleshooting.

---

## 1. Boot Process Deep Dive

Understanding how Linux boots is the first step in diagnosing "won't start" issues.

### 1.1 Firmware: BIOS vs UEFI
*   **Legacy BIOS (Basic Input/Output System)**:
    *   Reads the first 512 bytes (**MBR**) of the boot device.
    *   Limited to 2.2TB drives (MBR limitation).
    *   *Troubleshooting*: Verify boot order. If MBR is corrupt, `grub-install` usually overwrites it.
*   **UEFI (Unified Extensible Firmware Interface)**:
    *   Reads `.efi` binaries from a special partition (ESP - EFI System Partition), usually mounted at `/boot/efi`.
    *   Supports GPT (Zettabytes size) and Secure Boot.
    *   *Troubleshooting*: Use `efibootmgr` from a live CD to fix boot entries if they vanish.

### 1.2 The Bootloader: GRUB2
Grand Unified Bootloader v2 is the standard.

*   **Config Location**: DO NOT edit `/boot/grub/grub.cfg` directly.
    *   **Edit Here**: `/etc/default/grub` (User preferences like timeouts, kernel args).
    *   **Or Here**: `/etc/grub.d/` (Scripts for custom entries).
    *   **Generate**: `grub2-mkconfig -o /boot/grub/grub.cfg` (or `/boot/efi/EFI/redhat/grub.cfg` for UEFI).
*   *Troubleshooting*:
    *   **Symptom**: System hangs at boot logo.
    *   **Fix**: Press `e` at GRUB menu. Remove `rhgb quiet` to see logs. Add `rd.break` to drop into a shell before root mounts.

### 1.3 Initramfs (Initial RAM Filesystem)
The kernel needs drivers (modules) to mount the root filesystem (e.g., ext4, LVM, encryption). These drivers live on the filesystem the kernel is trying to mount! **Catch-22.**
*   **Solution**: Initramfs is a tiny CPIO archive loaded into RAM. It contains just enough modules to mount `/`.
*   **Management**:
    *   `lsinitrd /boot/initramfs-$(uname -r).img`: View contents.
    *   `dracut -f`: Rebuilds the image (RHEL).
    *   `mkinitrd`: Older tool, often a wrapper for dracut now.
*   *Troubleshooting*:
    *   **Symptom**: "Kernel panic - not syncing: VFS: Unable to mount root fs".
    *   **Cause**: Missing storage driver in initramfs (e.g., after physical server move).
    *   **Fix**: Boot rescue, rebuild initramfs with `dracut --add-drivers "module"`.

### 1.4 Systemd Initialization
Once root is mounted, kernel starts PID 1 (`/usr/lib/systemd/systemd`).

*   **Targets**:
    *   `multi-user.target` ~ Runlevel 3 (CLI).
    *   `graphical.target` ~ Runlevel 5 (GUI).
*   **Analysis**:
    *   `systemd-analyze verify default.target`: Check for restart loops.
    *   `systemd-analyze blame`: Identify slow services (boot performance).

---

## 2. Kernel Space vs User Space

The CPU rings protect the hardware.
*   **Ring 0**: Kernel Space (Full access).
*   **Ring 3**: User Space (Restricted).

### 2.1 System Calls (Syscalls)
Applications cannot access hardware (disk, network) directly. They ask the kernel via syscalls (e.g., `open`, `read`, `write`, `fork`).

*   *Troubleshooting with `strace`*:
    *   **Scenario**: Web server returns "500 Error" but logs are empty.
    *   **Command**: `strace -p <PID> -e trace=file`
    *   **Result**: You see `open("/var/www/html/config.php", O_RDONLY) = -1 EACCES (Permission Denied)`.
    *   **Diagnosis**: Permission issue not logged by the app.

### 2.2 Kernel Modules
The Linux kernel is monolithic but strict. Code is loaded dynamically as `.ko` files.

*   **Commands**:
    *   `lsmod`: List loaded modules.
    *   `modprobe <module>`: Load a module (and dependencies).
    *   `modinfo <module>`: Show details/parameters.
*   *Troubleshooting*:
    *   **Symptom**: Network card not found.
    *   **Fix**: Check `lspci -k` to see kernel driver in use. If missing, find vendor module.

### 2.3 Pseudo-Filesystems: /proc and /sys
They don't exist on disk; they are windows into the kernel's memory.
*   **/proc**: Process info & tunables. (`cat /proc/meminfo`, `echo 1 > /proc/sys/net/ipv4/ip_forward`).
*   **/sys**: Hardware info. (`/sys/class/net`, `/sys/block/sda`).

### 2.4 IPC (Inter-Process Communication)
*   **Pipes**: `|` connects stdout to stdin. Data flows unidirectionally in kernel memory buffers.
*   **Sockets**: Unix sockets (`/tmp/mysql.sock`) or TCP sockets. Faster than TCP loopback.
*   **Shared Memory**: Fastest IPC. Processes map the same RAM block.
*   *Troubleshooting*: use `ipcs -m` to view stuck shared memory segments after a crash.

---

## 3. Memory Management

### 3.1 Virtual Memory
Every process thinks it has 4GB (32-bit) or Huge (64-bit) RAM starting from 0x0. The **MMU (Memory Management Unit)** maps these Virtual Addresses to Physical RAM Frames.
*   **Swapping**: When RAM is full, LRU (Least Recently Used) pages move to disk.
*   **Thrashing**: Constant swapping. System becomes unresponsive.

### 3.2 Caches: Page vs. Buffer
*   **Page Cache**: Caches file contents. (Most of your "Used" RAM is usually this).
    *   *Benefit*: Repeated reads come from RAM.
*   **Buffer Cache**: Caches filesystem metadata (inode locations, block maps).
*   **Diagnosis**: `free -m`. "Available" includes Reclaimable Page Cache. If *Available* is low, you have a problem.

### 3.3 OOM Killer (Out Of Memory)
When RAM + Swap is exhausted, the kernel **must** kill something to survive.
*   **Selection**: High `oom_score` (based on RAM usage).
*   **Logs**: Check `/var/log/kern.log` or `dmesg` for "Killed process".
*   *Tuning*:
    *   Protect critical daemon: `echo -1000 > /proc/<PID>/oom_score_adj`.
    *   `vm.overcommit_memory`: Control if kernel promises more RAM than exists.

### 3.4 Hugepages
Standard page size is 4KB. For 100GB RAM, managing millions of pages is CPU overhead (TLB misses).
*   **Hugepages**: 2MB or 1GB pages.
*   **Use Case**: Databases (Oracle, Postgres), Java Heap. Pre-allocates RAM, preventing OOM for that portion and reducing CPU load.

---

## 4. Filesystem Layers

### 4.1 VFS (Virtual Filesystem Switch)
An abstraction layer. `cp` command doesn't know if it's writing to ext4, NFS, or FAT32. It talks to VFS, which talks to the driver.

### 4.2 Inodes
The DNA of a file. Contains: Permissions, Owner, Size, Timestamps, Disk Block pointers. **Filename is NOT in the inode** (it's in the directory list).
*   *Troubleshooting*:
    *   **Symptom**: "No space left on device" but `df -h` says 50% free.
    *   **Diagnosis**: Run `df -i`. You ran out of inodes (too many tiny files).

### 4.3 Journaling
Prevents corruption.
1.  Write "I am about to write data X to location Y" to Journal.
2.  Write data X to location Y.
3.  Mark Journal entry "Done".
*   **Crash**: On reboot, replay unfinished journal entries.
*   **Barrier**: `mount -o barrier=1` (Default). Ensures Journal is written to persistent media before Data. Disabling gains speed but risks data on power loss.

### 4.4 Mount Options & Performance
*   **noatime**: Don't update "Access Time" on every read. Huge write reduction for read-heavy servers.
*   **nodiratime**: Same for directories.
*   **discard**: (SSD) Issue TRIM commands immediately. Can be slow. Preferred: use periodic `fstrim` cron job.

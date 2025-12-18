# Linux Process Management for Enterprise Systems

**Level:** Expert / Senior Administrator
**Focus:** Lifecycle, Scheduling, and Performance Diagnostics via CLI.

---

## 1. Process States and Lifecycle

Processes transition through a state machine managed by the kernel scheduler.

### 1.1 The Five States (`stat` column in ps)

| Code | State | Description | Troubleshooting Context |
| :--- | :--- | :--- | :--- |
| **R** | **Running/Runnable** | Currently executed on a CPU or sitting in the run-queue waiting for a timeslice. | High load + High CPU usage = CPU saturation or infinite loop. |
| **S** | **Sleeping (Interruptible)** | Waiting for an event (e.g., user input, network packet, timer). can be woken by signals. | Most processes should be here. If a process is 'S' but unresponsive, it might be deadlocked on a lock in user-space. |
| **D** | **Uninterruptible Sleep** | Waiting for Hardware I/O (Disk/Network). **Cannot be killed** (even with -9) because the kernel needs the I/O to return to keep data consistent. | High load + Low CPU usage. Often indicates faulty storage, sad NFS mount, or overloaded swaps. |
| **Z** | **Zombie** | Process has terminated, but parent hasn't collected exit status via `wait()`. Uses no memory/CPU, only a PID slot. | Accumulation indicates buggy parent code. |
| **T** | **Stopped** | Paused by signal (SIGSTOP/SIGTSTP) or debugger (ptrace). | User hit Ctrl+Z or debugger is attached. |

### 1.2 State Transitions
1.  **Fork()**: Parent creates Child (State: R).
2.  **Scheduler**: Picks Child (State: R -> CPU).
3.  **IO Request**: Child asks for disk read (State: R -> D).
4.  **IO Complete**: Disk interrupts CPU (State: D -> R).
5.  **Exit**: Child finishes (State: R -> Z).
6.  **Reap**: Parent reads exit code (State: Z -> Removed).

---

## 2. CPU Scheduling Methods

### 2.1 CFS (Completely Fair Scheduler)
The default scheduler (since kernel 2.6.23).
*   **Goal**: Distribute CPU time "fairly" among processes.
*   **Mechanism**: Uses a Red-Black tree to track `vruntime` (virtual runtime). Processes with lowest `vruntime` get picked next.
*   **Latency vs. Throughput**: Tunable via `/proc/sys/kernel/sched_latency_ns`.

### 2.2 Prioritization (Nice Values)
*   **NI (Nice)**: User-space value range **-20** (Highest priority) to **19** (Lowest). Default is 0.
*   **PR (Priority)**: Kernel view. `PR = 20 + NI`.
    *   Range: 0 to 39 (Standard processes).
    *   RT classes show as `rt` or negative numbers in top.
*   **Command**: `renice -n -5 -p 1234`.

### 2.3 Real-Time Scheduling
For tasks needing deterministic timing (Audio, Industrial control).
*   **SCHED_FIFO**: First-In-First-Out. Runs until it yields or blocks. **Can freeze system** if it loops.
*   **SCHED_RR**: Round Robin. Like FIFO but with time slices.
*   **Tool**: `chrt -f 99 <command>`.

### 2.4 Affinity & Isolation
*   **Affinity**: Binding a process to specific cores to avoid cache misses.
    *   `taskset -c 0,1 ./app`: Run app on cores 0 and 1.
*   **Cgroups**: Limit total CPU usage (e.g., Docker/Kubernetes). A process might be "R" but stopped by throttling.

---

## 3. Process Relationships

### 3.1 Hierarchy
*   **PID 1 (systemd/init)**: The ancestor.
*   **Parent/Child**: Child inherits env. If parent dies, child becomes an **Orphan** and is re-parented to PID 1.
*   **Process Group (PGID)**: A shell pipeline `ls | grep | sort` forms a group. Access to shared IO.

### 3.2 Daemons
*   **Characteristics**: Parent is 1, no controlling terminal (TTY = ?), new session leader `setsid()`.
*   **Double Fork**: Common technique to create daemons (Parent forks middle, Middle forks daemon and exits, Daemon is orphaned to Init).

---

## 4. Monitoring Commands Reference

### 4.1 `ps` (Snapshot)
*   **Standard**: `ps aux` (BSD style).
    *   `RSS`: Real memory (Resident Set Size).
    *   `VSZ`: Virtual memory (includes libraries).
*   **Custom**: `ps -eo pid,ppid,state,ni,pcpu,cmd --sort=-pcpu | head`

### 4.2 `top` / `htop` (Real-time)
*   **Load Average**: Average number of processes in **R** (CPU queue) or **D** (Disk queue) states over 1, 5, 15 mins.
    *   Load > Cores = Saturation.
*   **CPU Line**:
    *   `us` (User): App code.
    *   `sy` (System): Kernel code (syscalls).
    *   `ni` (Nice): Low priority user code.
    *   `id` (Idle): Doing nothing.
    *   `wa` (Wait): Waiting for Disk I/O (correlated with **D** state).
    *   `si/hi` (Interrupts): Hardware/Software IRQs.
    *   `st` (Steal): Time stolen by Hypervisor (VMs only).

### 4.3 `pidstat` (Per-Process History)
Part of `sysstat` package. Excellent for finding "Who did X 5 minutes ago?".
*   `pidstat -u 1`: CPU stats every second.
*   `pidstat -d 1`: Disk I/O per process (Find who is causing Wait I/O).

### 4.4 `perf` (Profiler)
*   `perf top`: See which kernel functions are consuming CPU cycles in real-time.

---

## 5. Diagnostic Case Studies

### 5.1 Scenario: High Load, Low CPU
*   **Symptoms**: Load average: 20.00. CPU Idle: 95%. System sluggish.
*   **Diagnosis**:
    1.  Run `top`. Check `%wa` (I/O Wait). If high, it's disk.
    2.  Check state column for **D**.
    3.  `ps auxf | grep ' D '`: Find specific PIDs stuck in D.
    4.  `dmesg | tail`: Look for "SCSI error" or "NFS server not responding".
*   **Cause**: Processes are queued waiting on disk, counting towards Load, but CPU is bored.

### 5.2 Scenario: Processes Stuck in D (Uninterruptible)
*   **Fix**: You cannot kill them. You must fix the underlying I/O.
    *   If NFS: `umount -f -l /mnt/share`.
    *   If Hardware: Reboot might be only option if driver is wedged.

### 5.3 Scenario: Zombie Apocalypse
*   **Symptoms**: `top` shows "50 zombie". PID count rising.
*   **Diagnosis**:
    1.  `ps -A -o stat,ppid,pid,cmd | grep -e '^[Zz]'`
    2.  Identify common PPID (Parent PID).
*   **Remediation**:
    *   Kill the **Parent**: `kill -15 <PPID>`. Init (1) will inherit zombies and clean them up instantly.
    *   Fix the parent's code (missing `wait()`).

### 5.4 Scenario: CPU Saturation
*   **Symptoms**: Sluggish terminal. Audio skipping.
*   **Diagnosis**:
    1.  `top`: `us` is 99%.
    2.  Identify offender.
*   **Analysis**:
    *   Is it one thread? (max 100% on one core). `H` (Threads) in htop.
    *   Is it kernel? (High `sy`). Use `perf top` to see if it's a spinlock issue.

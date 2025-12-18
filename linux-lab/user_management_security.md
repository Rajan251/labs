# Linux User Management & Security Permutations Guide

**Chapter:** 2
**Focus:** Security Hardening & Access Control
**Goal:** Master ACLs, sudoers, and advanced file ownership.

---

## 1. The Sudoers File: Safe Delegation

The `/etc/sudoers` file controls who can run what as superuser. **Never edit this file with a standard text editor.**

### Using `visudo`
Always use the `visudo` command. It locks the file against simultaneous edits and validates syntax before saving, preventing you from locking yourself out of root.

```bash
sudo visudo
```

### Password-less Commands
Sometimes you need a user to run a specific script without a password (e.g., for automation), but you don't want to give them full root access.

**Syntax:** `User_Name Host_Alias=(User_Run_As) NOPASSWD: /path/to/command`

**Example:** Allow user `deploy` to restart Nginx without a password.
```text
deploy ALL=(root) NOPASSWD: /usr/sbin/service nginx restart
```

### Aliases for Organization
Grouping users and commands makes the file readable.

```text
# User Alias
User_Alias ADMINS = alice, bob, charlie

# Command Alias
Cmnd_Alias NETWORKING = /bin/ping, /sbin/ifconfig, /usr/bin/ip

# Rule
ADMINS ALL=(root) NETWORKING
```

---

## 2. Standard Permissions

Linux permissions are defined for three categories: **User (u)**, **Group (g)**, and **Others (o)**.

### `chmod`: Changing Modes

**Symbolic Mode:** Easier to remember.
*   `chmod u+x script.sh` (Add executable to user)
*   `chmod g-w file.txt` (Remove write from group)
*   `chmod o= file.txt` (Remove all permissions from others)

**Octal Mode:** Faster for absolute settings.
*   Read=4, Write=2, Execute=1.

| value | Permission | Typical Use (File) | Typical Use (Dir) |
| :--- | :--- | :--- | :--- |
| **755** | `rwxr-xr-x` | Scripts/Binaries | Public Directories |
| **644** | `rw-r--r--` | Config files | N/A |
| **600** | `rw-------` | SSH Keys, Secrets | N/A |
| **777** | `rwxrwxrwx` | **NEVER** in production | **NEVER** in production |

### `chown` and `chgrp`
*   **Change Owner:** `chown user file`
*   **Change Group:** `chgrp group file`
*   **Recursive Change:** `chown -R user:group /var/www/html`

---

## 3. Advanced Permissions

When standards `rwx` aren't enough, we use special flags.

### SetUID (SUID) - `s`
executes a file with the permissions of the **file owner**, not the user running it.
*   **Example:** `/usr/bin/passwd` needs to write to `/etc/shadow` (owned by root), even when run by a standard user.
*   **Security Risk:** If a SUID binary has a vulnerability, an attacker can escalate to root.
*   **Set:** `chmod u+s /path/to/file` (Shows as `rws`)

### SetGID (SGID) - `s`
*   **On Files:** Runs with permissions of the **file group**.
*   **On Directories:** New files created inside inherit the **directory's group**, not the creator's default group. Crucial for shared team folders.
*   **Set:** `chmod g+s /path/to/directory`

### Sticky Bit - `t`
Used on shared directories like `/tmp`. It ensures that **only the file owner** (or root) can delete a file, even if others have write permission to the directory.
*   **Set:** `chmod +t /tmp` (Shows as `rwt` at the end)

---

## 4. ACLs (Access Control Lists)

Standard permissions only allow one owner and one group. ACLs allow you to give permission to *specific* extra users or groups.

**Prerequisite:** Ensure `acl` package is installed.

### `setfacl`: Setting Permissions
**Scenario:** `file.txt` is owned by `alice:devs`. You want `bob` (who is not in `devs`) to have read access.

```bash
setfacl -m u:bob:r file.txt
```
*   `-m`: Modify
*   `u:bob:r`: User bob gets read.

**Recursive Default ACL:**
Ensure all *new* files in a directory automatically get specific permissions.
```bash
setfacl -R -m d:u:bob:rwx /shared/project
```

### `getfacl`: Viewing Permissions
`ls -l` will show a `+` sign (e.g., `-rw-rwxr--+`) indicating ACLs exist.

```bash
getfacl file.txt
```

---

## 5. Troubleshooting

### Locked Out Root Account
If you broke sudo or lost the root password:
1.  **Reboot** the machine.
2.  At the **GRUB menu**, press `e` to edit the boot entry.
3.  Find the line starting with `linux` or `linux16`.
4.  Append `init=/bin/bash` or `rd.break` to the end of that line.
5.  Press `Ctrl+X` to boot.
6.  Remount root as read-write: `mount -o remount,rw /`
7.  Reset password: `passwd root`
8.  Reboot: `exec /sbin/init`

### "sudo: command not found"
1.  **Check Path:** `echo $PATH`. `/usr/bin` and `/usr/sbin` must be present.
2.  **Check Installation:** It might actually be missing (e.g., in minimal Docker containers).
    *   `apt-get install sudo` OR `yum install sudo`
    *   Log in as root (`su -`) to install it if you are a normal user without sudo.

# Layered Security Approach for Production Linux

**Level:** Expert / Security Engineer
**Focus:** Defense in Depth (Kernel, Network, Auth, Data).

---

## 1. Kernel Security Modules

### 1.1 SELinux (Security Enhanced Linux)
*   **Concept**: Mandatory Access Control (MAC). Every process and file has a **Context** (User:Role:Type:Level). Rules define which *Domain* (process type) can access which *Type* (file type).
*   **Modes**:
    *   `Enforcing`: Blocks and logs.
    *   `Permissive`: Logs only (Great for debugging).
    *   `Disabled`: Off (Requires reboot).
*   **Troubleshooting**:
    *   **Log**: `/var/log/audit/audit.log`.
    *   **Tool**: `audit2allow -w -a` (Explains why access was denied in human terms).
    *   **Fix**: `chcon` (Change context temporary) or `semanage fcontext` (Permanent).
    *   *Common Issue*: Apache cannot read `/var/www/html/custom`. Fix: `restorecon -Rv /var/www/html`.

### 1.2 AppArmor
*   **Concept**: Profile-based MAC. loaded per-binary path. Easier to read than SELinux but less granular (Path based vs Inode based).
*   **Profiles**: `/etc/apparmor.d/`.
*   **Modes**: Enforce vs Complain.

### 1.3 Seccomp (Secure Computing Mode)
*   **Function**: Restricts the System Calls a process can make.
*   **Use Case**: A web server shouldn't need to call `mount()` or `ptrace()`.
*   **Implementation**: Often handled by Systemd (`SystemCallFilter=`) or Container Runtimes (Docker default profile).

---

## 2. Authentication and Authorization

### 2.1 PAM (Pluggable Authentication Modules)
Architecture for dynamic auth.
*   **Config**: `/etc/pam.d/`.
*   **Modules**:
    *   `pam_unix.so`: Standard /etc/shadow.
    *   `pam_faillock.so`: Lockout after N failed attempts.
    *   `pam_google_authenticator.so`: MFA.

### 2.2 SSSD (System Security Services Daemon)
The enterprise standard for joining Linux to LDAP/AD/Kerberos.
*   **Feature**: Offline Caching. If AD is down, users can still login if they cached credentials previously.
*   **Config**: `/etc/sssd/sssd.conf`.

### 2.3 Sudoers Best Practices
*   **No Shell Escapes**: Prevent users from breaking out of limited commands.
    *   `alice ALL=(root) NOEXEC: /usr/bin/vim` (Prevents running shell from inside vim).
*   **Aliases**: Use `Cmnd_Alias` to group dangerous commands.

---

## 3. Network Security Layers

### 3.1 Firewall Strategy
*   **Default Deny**: Drop everything. Allow only what is needed.
*   **Zones (FirewallD)**: Assign interfaces to zones (Public, Internal, DMZ).
*   **Rich Rules**: Complex logic. `firewall-cmd --add-rich-rule='rule family="ipv4" source address="192.168.1.0/24" service name="ssh" accept'`.

### 3.2 Network Segmentation
*   **VLANs**: L2 isolation.
*   **Firewall between VLANS**: Never route traffic directly.
*   **Micro-segmentation**: Host-based firewalls (iptables) preventing lateral movement (DB should only accept from App, not other DBs).

### 3.3 VPNs
*   **IPsec (StrongSwan/Libreswan)**: Industry standard, complex, kernel-space. Interoperable with hardware firewalls.
*   **WireGuard**: Modern, extremely fast, kernel-space (Linux 5.6+). Uses public keys. Easier to audit source code.
*   **Certificates**: Automate rotation with **Certbot** (Let's Encrypt) or **HashiCorp Vault**.

---

## 4. Filesystem Security

### 4.1 Attributes
Beyond `chmod`.
*   `chattr +i file`: **Immutable**. Even root cannot delete/modify until attribute is removed. Good for logs/binaries.
*   `chattr +a file`: **Append-only**. Good for log files.

### 4.2 Encryption
*   **LUKS (Linux Unified Key Setup)**: Full Disk Encryption (At rest).
    *   `cryptsetup luksFormat /dev/sdb1`.
    *   Use **Clevis/Tang** for automated network-bound decryption (booting servers without typing passwords).
*   **eCryptfs**: Directory level encryption (User home dirs).

### 4.3 Audit Subsystem (`auditd`)
*   **Role**: The flight recorder.
*   **Rules**:
    *   `-w /etc/passwd -p wa -k identity`: Log writes/attribute-changes to password file.
    *   `-a always,exit -F arch=b64 -S execve`: Log every command executed.

---

## 5. Container Security

### 5.1 Namespace Isolation
Namespaces (PID, NET, MNT) are not perfect boundaries. Root in a container is Root on the host (share kernel).

### 5.2 User Namespaces (`userns`)
**Crucial defense**. Maps `root (0)` inside container to `nobody (65534)` outside.
*   If attacker breaks out, they are a powerless user on the host.

### 5.3 Capabilities
Linux breaks "Root" power into ~40 capabilities (`CAP_CHOWN`, `CAP_NET_ADMIN`).
*   **Strategy**: Drop ALL, add back only needed.
*   **Drop**: `CAP_SYS_ADMIN` (The god mode), `CAP_NET_RAW` (Ping/Spoofing).

---

## 6. Incident Response Procedures

### 6.1 Preparation
*   Have static binaries (`ls`, `ps`, `netstat`, `dd`) ready on a trusted USB/Read-Only mount. (In case attackers trojaned system binaries).

### 6.2 Forensic Collection Checklist
1.  **Volatile Data** (Capture first!):
    *   RAM dump (`LiME` or `dd /dev/mem` if capable).
    *   Network connections (`ss -antup`).
    *   Running processes (`ps auxwf`).
2.  **Non-Volatile Data**:
    *   Disk Image (`dd if=/dev/sda of=/mnt/evidence/disk.img`).
    *   Logs (`/var/log`).

### 6.3 Timeline Analysis
Attackers touch files.
*   **MAC Times**: Modified, Accessed, Changed times.
*   **Tool**: `log2timeline` (Plaso). Correlates syslog, audit.log, and filesystem metadata into a single chronological CSV.

---

## 7. Compliance Mappings

| Requirement | **PCI-DSS (Payment)** | **HIPAA (Health)** | **NIST CSF** | **Linux Implementation** |
| :--- | :--- | :--- | :--- | :--- |
| **Audit/Logging** | Req 10: Track access | §164.312(b): Audit control | Detect (DE.AE) | `auditd`, Remote Syslog, FIM (`aide`) |
| **Access Control** | Req 7: Need-to-know | §164.312(a): Unique ID | Protect (PR.AC) | SSSD, MFA, SELinux, User Namespaces |
| **Encryption** | Req 3: Protect data | §164.312(a)(2)(iv): Encryption | Protect (PR.DS) | LUKS (At Rest), TLS 1.3 (Transit) |
| **Vulnerability** | Req 6: Patching | §164.308(a)(5): Integrity | Protect (PR.MA) | Automated Updates (`dnf-automatic`), Kernel Live Patching |
| **Fail2Ban/IPS** | Req 11: Intrusion det | §164.308(a)(1): Risk Analysis | Detect (DE.CM) | Fail2Ban, FirewallD Rich Rules |

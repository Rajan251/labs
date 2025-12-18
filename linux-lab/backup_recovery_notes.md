# Backup & Recovery Methodology

**Level:** Expert / Systems Administrator
**Focus:** Data protection, disaster recovery, and business continuity.

---

## 1. Backup Strategy Fundamentals

### 1.1 The 3-2-1 Rule
*   **3 Copies**: Original + 2 backups.
*   **2 Media Types**: Disk + Tape (or Cloud).
*   **1 Offsite**: Protection against site disasters (fire, flood).

### 1.2 RPO vs RTO
*   **RPO (Recovery Point Objective)**: Maximum acceptable data loss. "We can lose 1 hour of data."
*   **RTO (Recovery Time Objective)**: Maximum acceptable downtime. "We must be back online in 4 hours."
*   **Trade-off**: Lower RPO/RTO = Higher cost (more frequent backups, faster storage).

### 1.3 Backup Types
| Type | Description | Storage | Restore Speed |
| :--- | :--- | :--- | :--- |
| **Full** | Complete copy of all data | High | Fast (single restore) |
| **Incremental** | Changes since last backup (any type) | Low | Slow (need full + all incrementals) |
| **Differential** | Changes since last full | Medium | Medium (need full + latest differential) |

---

## 2. Filesystem-Level Backups

### 2.1 Snapshot-Based Backups
*   **LVM Snapshots**:
    ```bash
    lvcreate -L 10G -s -n backup_snap /dev/vg0/data
    mount /dev/vg0/backup_snap /mnt/snap
    tar czf /backup/data.tar.gz -C /mnt/snap .
    umount /mnt/snap
    lvremove -f /dev/vg0/backup_snap
    ```
    *   **Pros**: Instant, consistent point-in-time.
    *   **Cons**: Performance impact while snapshot exists.
*   **ZFS/Btrfs**: Native CoW snapshots. Zero overhead.

### 2.2 rsync with Hardlinks
*   **rsnapshot**: Creates daily/weekly/monthly snapshots using hardlinks.
    ```bash
    rsync -a --link-dest=/backup/daily.0 /data/ /backup/daily.1/
    ```
    *   **Benefit**: Space-efficient. Unchanged files are hardlinked, not copied.

### 2.3 Open File Handling
*   **Problem**: Backing up a database file while it's being written = corrupt backup.
*   **Solution**: LVM snapshot or `fsfreeze` before backup.

---

## 3. Database Backup Methods

### 3.1 Logical Backups
*   **mysqldump**, **pg_dump**: Export to SQL.
*   **Pros**: Portable, human-readable, version-independent.
*   **Cons**: Slow restore (replay SQL), locks tables.

### 3.2 Physical Backups
*   **Percona XtraBackup** (MySQL), **pg_basebackup** (PostgreSQL): Copy data files.
*   **Pros**: Fast restore.
*   **Cons**: Binary compatibility required.

### 3.3 Point-in-Time Recovery (PITR)
*   **MySQL**: Base backup + Binary logs.
*   **PostgreSQL**: Base backup + WAL (Write-Ahead Log).
*   **Process**:
    1.  Restore base backup (e.g., from Sunday).
    2.  Replay logs up to desired timestamp (e.g., Tuesday 14:55).

---

## 4. System State Backup

### 4.1 Configuration vs Backup
*   **Configuration Management** (Ansible, Puppet): Rebuilds system from code.
*   **Backup**: Captures exact state (faster recovery, but less flexible).

### 4.2 Package State
```bash
# RHEL/CentOS
rpm -qa > /backup/packages.txt
# Debian/Ubuntu
dpkg --get-selections > /backup/packages.txt
```

### 4.3 User and Permissions
*   Backup `/etc/passwd`, `/etc/shadow`, `/etc/group`.
*   Use `getfacl -R /` to preserve ACLs.

---

## 5. Recovery Procedures

### 5.1 Bare Metal Recovery
1.  Boot from rescue media (Live CD).
2.  Partition disks identically.
3.  Restore system files: `tar xzf /backup/system.tar.gz -C /mnt`.
4.  Chroot: `chroot /mnt`.
5.  Reinstall bootloader: `grub-install /dev/sda`.
6.  Reboot.

### 5.2 Individual File Restoration
```bash
tar xzf /backup/data.tar.gz ./path/to/file
```

### 5.3 Database PITR
```bash
# MySQL
mysql < base_backup.sql
mysqlbinlog --stop-datetime="2025-12-18 14:55:00" binlog.* | mysql
```

---

## 6. Testing and Validation

### 6.1 Regular Testing Schedule
*   **Monthly**: Full restore drill.
*   **Quarterly**: Bare metal recovery test.
*   **Annually**: Disaster recovery simulation (entire datacenter failure).

### 6.2 Automated Verification
*   **Checksum Validation**: Verify backup integrity.
*   **Test Restore**: Automated script restores to staging environment.

---

## 7. Cloud and Hybrid Considerations

### 7.1 Snapshot Strategies
*   **AWS EBS**: Snapshots are incremental, stored in S3.
*   **GCP Persistent Disk**: Snapshots are global (cross-region).

### 7.2 Storage Tiers
| Tier | Cost | Retrieval Time | Use Case |
| :--- | :--- | :--- | :--- |
| **Hot** (S3 Standard) | High | Instant | Active backups (last 30 days) |
| **Cold** (Glacier) | Low | Hours | Archive (compliance, 7+ years) |

### 7.3 Compliance
*   **GDPR**: Data must stay in EU (use region restrictions).
*   **HIPAA**: Encryption at rest and in transit mandatory.

---

## 8. Decision Matrices

### 8.1 Backup Frequency
| RPO | Backup Frequency |
| :--- | :--- |
| 24 hours | Daily |
| 1 hour | Hourly |
| 5 minutes | Continuous (replication) |

### 8.2 Retention Period
| Data Type | Retention |
| :--- | :--- |
| Production DB | 30 days |
| Logs | 90 days |
| Financial Records | 7 years (legal) |

### 8.3 Encryption Requirements
*   **Sensitive Data** (PII, PHI): Always encrypt.
*   **Public Data**: Optional (performance trade-off).

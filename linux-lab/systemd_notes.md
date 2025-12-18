# Systemd for Production Operations

**Level:** Expert / DevOps Engineer
**Focus:** Service management, resource control, and security hardening.

---

## 1. Unit File Anatomy

Systemd units are defined in `.service`, `.socket`, `.timer`, etc. files.

### 1.1 [Unit] Section
Common to all unit types.
```ini
[Unit]
Description=My Application Server
Documentation=https://example.com/docs
After=network-online.target
Wants=network-online.target
```
*   **After=**: Start this unit after the specified units (ordering only, not dependency).
*   **Wants=**: Weak dependency. If target fails, this unit still starts.

### 1.2 [Service] Section
Defines how the service runs.
```ini
[Service]
Type=notify
ExecStart=/usr/bin/myapp --config /etc/myapp.conf
Restart=on-failure
RestartSec=5s
User=myapp
Group=myapp
```
*   **Type**:
    *   `simple`: Default. Process started by ExecStart is the main process.
    *   `forking`: Process forks and parent exits. Systemd tracks the child (requires PIDFile).
    *   `notify`: Process sends readiness notification via `sd_notify()` (PostgreSQL, Nginx).
    *   `oneshot`: Runs once and exits (scripts). Use `RemainAfterExit=yes` to keep unit "active".

### 1.3 [Install] Section
Controls enabling/disabling.
```ini
[Install]
WantedBy=multi-user.target
```
*   `systemctl enable myapp` creates symlink in `/etc/systemd/system/multi-user.target.wants/`.

### 1.4 Drop-in Files
Override or extend without editing the original unit.
*   **Path**: `/etc/systemd/system/myapp.service.d/override.conf`
*   **Example**:
```ini
[Service]
Environment="DEBUG=1"
```
*   **Reload**: `systemctl daemon-reload`.

---

## 2. Service Lifecycle Management

### 2.1 Dependencies
*   **Requires=**: Hard dependency. If dependency fails, this unit fails.
*   **Wants=**: Soft dependency. Recommended for most cases.
*   **BindsTo=**: Like Requires, but also stops this unit if dependency stops.

### 2.2 Ordering
*   **Before=**: This unit must start before the specified units.
*   **After=**: This unit starts after the specified units.
*   *Note*: Ordering does NOT imply dependency. Use both `After=` and `Wants=` together.

### 2.3 Failure Handling
```ini
[Service]
Restart=on-failure
RestartSec=10s
StartLimitBurst=5
StartLimitIntervalSec=60s
```
*   If service fails 5 times in 60 seconds, systemd gives up.

### 2.4 Watchdog
For services that support it (PostgreSQL, Nginx with modules).
```ini
[Service]
WatchdogSec=30s
```
*   Service must call `sd_notify("WATCHDOG=1")` every 30s or systemd restarts it.

---

## 3. Resource Control (cgroups v2)

Systemd uses cgroups to limit resources.

### 3.1 CPU Limiting
```ini
[Service]
CPUAccounting=true
CPUQuota=50%
```
*   Limits service to 50% of one CPU core (0.5 cores).

### 3.2 Memory Limiting
```ini
[Service]
MemoryAccounting=true
MemoryMax=1G
MemorySwapMax=0
```
*   Hard limit at 1GB. Disable swap for this service.

### 3.3 IO Control
```ini
[Service]
IOAccounting=true
IOWeight=500
IOReadBandwidthMax=/dev/sda 10M
```
*   Weight: 1-10000 (default 100). Higher = more priority.
*   Bandwidth: Limit reads to 10MB/s.

---

## 4. Journal Management

### 4.1 Structured Logging
Journald stores logs in binary format with metadata.
*   **Query**: `journalctl -u myapp.service --since "2 hours ago" -o json-pretty`.

### 4.2 Forwarding to Syslog
```ini
# /etc/systemd/journald.conf
[Journal]
ForwardToSyslog=yes
```
*   Sends logs to rsyslog for centralized logging.

### 4.3 Retention
```ini
[Journal]
SystemMaxUse=500M
MaxRetentionSec=1month
```
*   Limits disk usage and age.

---

## 5. Security Features

### 5.1 Sandboxing
```ini
[Service]
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadOnlyPaths=/etc /usr
ReadWritePaths=/var/lib/myapp
```
*   **PrivateTmp**: Service gets its own `/tmp`.
*   **ProtectSystem**: Makes `/usr`, `/boot`, `/efi` read-only.

### 5.2 Capability Reduction
```ini
[Service]
CapabilityBoundingSet=CAP_NET_BIND_SERVICE
AmbientCapabilities=CAP_NET_BIND_SERVICE
```
*   Allows binding to ports <1024 without running as root.

### 5.3 Syscall Filtering
```ini
[Service]
SystemCallFilter=@system-service
SystemCallFilter=~@privileged @resources
```
*   Whitelist common syscalls, blacklist dangerous ones.

### 5.4 User Switching
```ini
[Service]
User=www-data
Group=www-data
NoNewPrivileges=true
```
*   Run as non-root. Prevent privilege escalation.

---

## 6. Troubleshooting

### 6.1 Boot Performance
```bash
systemd-analyze blame
systemd-analyze critical-chain
```
*   Shows which units took longest to start.

### 6.2 Service Status
```bash
systemctl status myapp.service
```
*   **Active: active (running)**: Main process is running.
*   **Active: active (exited)**: Type=oneshot completed successfully.
*   **Active: failed**: Service crashed.

### 6.3 Dependency Visualization
```bash
systemd-analyze dot myapp.service | dot -Tsvg > graph.svg
```
*   Generates a visual dependency graph.

### 6.4 Emergency Recovery
If systemd itself fails to boot:
1.  Add `systemd.unit=rescue.target` to kernel command line (GRUB).
2.  Or `systemd.unit=emergency.target` for minimal shell.

---

## 7. Common Patterns

### 7.1 Database (PostgreSQL)
```ini
[Unit]
Description=PostgreSQL Database
After=network.target

[Service]
Type=notify
User=postgres
ExecStart=/usr/bin/postgres -D /var/lib/postgres/data
Restart=always
TimeoutSec=300

[Install]
WantedBy=multi-user.target
```

### 7.2 Web Application (Gunicorn)
```ini
[Unit]
Description=Gunicorn for MyApp
After=network-online.target
Wants=network-online.target

[Service]
Type=notify
WorkingDirectory=/opt/myapp
ExecStart=/opt/myapp/venv/bin/gunicorn -w 4 myapp:app
Restart=on-failure
User=www-data

[Install]
WantedBy=multi-user.target
```

### 7.3 Batch Job (Backup Script)
```ini
[Unit]
Description=Nightly Backup

[Service]
Type=oneshot
ExecStart=/usr/local/bin/backup.sh
User=backup
```
*   Triggered by a `.timer` unit (systemd's cron replacement).

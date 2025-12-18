# find - Search for Files and Directories

**COMMAND NAME**: find (pronounced "find")  
**SYNOPSIS**: `find [path...] [expression]`  
**CATEGORY**: File Management

---

## PURPOSE & REAL-WORLD USE CASES

**Primary Function**: Recursively search directory trees for files matching specified criteria.

**Common Organizational Use Cases**:
- **Security Audits**: Find files with dangerous permissions (SetUID, world-writable)
- **Compliance**: Locate files older than retention policy allows
- **Cleanup**: Identify large files consuming disk space
- **Backup Verification**: Find files modified since last backup
- **Incident Response**: Locate recently modified files during security investigation

**When to Choose Over Alternatives**:
- Use `find` for: Complex searches, recursive operations, executing actions on results
- Use `locate` for: Fast filename searches (uses database, not real-time)
- Use `ls` for: Simple directory listings without recursion

---

## OPTION BREAKDOWN (Top 20 Options)

### Search Criteria

**-name pattern**: Match filename (case-sensitive)
```bash
find /var/log -name "*.log"
# Output: /var/log/syslog, /var/log/auth.log, etc.
```

**-iname pattern**: Match filename (case-insensitive)
```bash
find /home -iname "readme.txt"
# Finds: README.txt, readme.TXT, ReadMe.txt
```

**-type [f|d|l]**: Filter by type (f=file, d=directory, l=symlink)
```bash
find /etc -type f -name "*.conf"
# Only finds files, not directories named *.conf
```

**-size [+|-]N[k|M|G]**: Match by size
```bash
find /var -size +100M
# Files larger than 100MB
```

**-mtime [+|-]N**: Modified N days ago
```bash
find /tmp -mtime +7
# Files modified more than 7 days ago
```

**-atime [+|-]N**: Accessed N days ago
```bash
find /home -atime -1
# Files accessed in last 24 hours
```

**-user username**: Files owned by user
```bash
find /home -user alice
# All files owned by alice
```

**-perm mode**: Files with exact permissions
```bash
find / -perm 4755
# Find SetUID files (security audit)
```

**-perm -mode**: Files with at least these permissions
```bash
find /var/www -perm -o+w
# World-writable files (security risk!)
```

### Actions

**-exec command {} \;**: Execute command on each result
```bash
find /tmp -name "*.tmp" -exec rm {} \;
# Delete all .tmp files
```

**-exec command {} +**: Execute command with multiple results (faster)
```bash
find /var/log -name "*.log" -exec grep "ERROR" {} +
# Grep ERROR in all log files (batched)
```

**-delete**: Delete matched files
```bash
find /tmp -type f -mtime +30 -delete
# Delete files older than 30 days
```

**-ls**: List in ls -dils format
```bash
find /etc -name "*.conf" -ls
# Detailed listing of config files
```

**-print0**: Null-separated output (safe for xargs)
```bash
find / -name "*.bak" -print0 | xargs -0 rm
# Safe deletion even with spaces in filenames
```

### Logical Operators

**-and / -a**: Logical AND (default)
```bash
find /var -type f -and -size +100M
# Files AND larger than 100MB
```

**-or / -o**: Logical OR
```bash
find /etc -name "*.conf" -or -name "*.cfg"
# .conf OR .cfg files
```

**-not / !**: Logical NOT
```bash
find /home -not -user root
# Files NOT owned by root
```

### Performance & Limits

**-maxdepth N**: Descend at most N levels
```bash
find /var -maxdepth 2 -name "*.log"
# Only search 2 levels deep (faster)
```

**-mindepth N**: Start at level N
```bash
find /home -mindepth 2 -name "*.txt"
# Skip /home itself, start at /home/user/
```

**-prune**: Don't descend into directory
```bash
find / -path /proc -prune -o -name "*.conf" -print
# Skip /proc directory entirely
```

---

## ORGANIZATIONAL PATTERNS

### Security Auditing
```bash
# Find SetUID/SetGID files (potential privilege escalation)
find / -type f \( -perm -4000 -o -perm -2000 \) -ls

# Find world-writable files (security risk)
find /var/www -type f -perm -o+w -ls

# Find files modified in last hour (incident response)
find /etc -mtime -0.04 -ls  # 0.04 days = 1 hour
```

### Compliance & Cleanup
```bash
# Delete logs older than 90 days (compliance)
find /var/log -name "*.log" -mtime +90 -delete

# Find large files for cleanup
find /home -type f -size +1G -exec ls -lh {} \; | sort -k5 -hr

# Archive old files
find /data -mtime +365 -exec tar -czf archive.tar.gz {} +
```

### Performance Optimization
```bash
# Use -maxdepth to limit recursion
find /var -maxdepth 3 -name "*.log"  # Faster than unlimited depth

# Use -print0 with xargs for parallel processing
find /data -name "*.txt" -print0 | xargs -0 -P 4 gzip
```

---

## ADVANCED TECHNIQUES

### Complex One-Liners
```bash
# Find and replace in multiple files
find /var/www -name "*.php" -exec sed -i 's/old/new/g' {} +

# Find duplicate files by size and MD5
find /home -type f -exec md5sum {} + | sort | uniq -w32 -dD

# Find files modified today and copy to backup
find /data -type f -mtime 0 -exec cp --parents {} /backup/ \;
```

### Scripting Integration
```bash
#!/bin/bash
# Automated cleanup script
THRESHOLD=90
find /var/log -name "*.log" -mtime +$THRESHOLD -print0 | \
  while IFS= read -r -d '' file; do
    echo "Deleting: $file"
    rm "$file"
  done
```

---

## TROUBLESHOOTING SCENARIOS

### Scenario 1: Disk Space Full
**Problem**: `/var` partition at 100%  
**Diagnosis**:
```bash
find /var -type f -size +100M -exec ls -lh {} \; | sort -k5 -hr | head -20
```
**Solution**: Delete or archive large files  
**Verification**:
```bash
df -h /var
```

### Scenario 2: Security Breach - Find Recently Modified Files
**Problem**: Suspected unauthorized access  
**Diagnosis**:
```bash
find /etc /var/www -type f -mtime -1 -ls
```
**Solution**: Review and restore from backup if needed  
**Verification**:
```bash
find /etc -newer /tmp/breach_timestamp -ls
```

### Scenario 3: Permission Issues
**Problem**: Web server can't write to upload directory  
**Diagnosis**:
```bash
find /var/www/uploads -type d ! -perm -o+w
```
**Solution**:
```bash
find /var/www/uploads -type d -exec chmod 775 {} \;
```
**Verification**:
```bash
find /var/www/uploads -type d -ls
```

---

## DANGERS & PITFALLS

⚠️ **-delete is irreversible**: Always test with `-print` first
```bash
# WRONG: Immediate deletion
find /tmp -name "*.tmp" -delete

# RIGHT: Test first
find /tmp -name "*.tmp" -print
# Then if output looks correct:
find /tmp -name "*.tmp" -delete
```

⚠️ **-exec without {} +**: Runs command for EACH file (slow)
```bash
# SLOW: One grep per file
find /var/log -name "*.log" -exec grep "ERROR" {} \;

# FAST: Batched grep
find /var/log -name "*.log" -exec grep "ERROR" {} +
```

⚠️ **Filename with spaces**: Use -print0 with xargs -0
```bash
# WRONG: Breaks on spaces
find /data -name "*.txt" | xargs rm

# RIGHT: Null-separated
find /data -name "*.txt" -print0 | xargs -0 rm
```

---

## RELATED COMMANDS & WHEN TO USE THEM

- **locate**: Use when you need fast filename search (uses database, updated daily)
- **fd**: Modern alternative with simpler syntax (not always installed)
- **grep -r**: Use when searching file CONTENTS, not names
- **ls -R**: Use for simple recursive listing without filtering

---

## MEMORY AIDS & TIPS

**Mnemonics**:
- **-mtime**: "Modified TIME"
- **-atime**: "Accessed TIME"
- **-ctime**: "Changed TIME" (metadata, not content)

**Useful Aliases**:
```bash
alias findf='find . -type f -name'
alias findd='find . -type d -name'
alias finds='find . -type f -size'
```

**Tab Completion**: Most shells support tab completion for find options

---

## EXERCISES FOR MASTERY

### Exercise 1: Beginner
**Task**: Find all `.log` files in `/var/log` modified in the last 7 days  
**Solution**:
```bash
find /var/log -name "*.log" -mtime -7
```

### Exercise 2: Intermediate
**Task**: Find all files larger than 50MB in `/home`, owned by user `alice`, and list them sorted by size  
**Solution**:
```bash
find /home -type f -size +50M -user alice -exec ls -lh {} \; | sort -k5 -hr
```

### Exercise 3: Advanced
**Task**: Find all SetUID files on the system, exclude `/proc` and `/sys`, and save to a report  
**Solution**:
```bash
find / \( -path /proc -o -path /sys \) -prune -o -type f -perm -4000 -ls > setuid_report.txt
```

---

## EXAMPLE OUTPUT WALKTHROUGH

```bash
$ find /etc -name "*.conf" -type f -mtime -7 -ls
```

**Output**:
```
1234567  4 -rw-r--r--  1 root root  1024 Dec 15 10:30 /etc/nginx/nginx.conf
2345678  8 -rw-r--r--  1 root root  4096 Dec 16 14:20 /etc/mysql/my.conf
```

**Explanation**:
- `1234567`: Inode number
- `4`: Blocks used
- `-rw-r--r--`: Permissions
- `1`: Hard link count
- `root root`: Owner and group
- `1024`: Size in bytes
- `Dec 15 10:30`: Modification time
- `/etc/nginx/nginx.conf`: Full path

---

## PERFORMANCE CONSIDERATIONS

**Time Complexity**: O(n) where n = number of files in directory tree  
**Memory Usage**: Minimal (processes one file at a time)  
**Disk I/O**: High (reads directory entries, can stress I/O on large filesystems)  
**Network**: N/A (local filesystem only)

**Optimization Tips**:
- Use `-maxdepth` to limit recursion
- Use `-prune` to skip unnecessary directories
- Use `{}` + instead of `{}` \; for batched execution

---

## COMPATIBILITY NOTES

**RHEL/CentOS**: GNU findutils (full feature set)  
**Ubuntu/Debian**: GNU findutils (identical to RHEL)  
**Alpine Linux**: BusyBox find (limited options, no -printf)  
**macOS**: BSD find (different -perm syntax, no -printf)

**Deprecated Options**:
- `-perm +mode`: Use `-perm /mode` instead (any bit match)

**Modern Alternatives**:
- `fd`: Faster, simpler syntax, but not standard on all systems

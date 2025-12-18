# Command Comparison: ps vs top vs htop

**Commands Compared**: Process monitoring tools  
**Category**: System Monitoring & Process Control

---

## DECISION TREE FOR COMMAND SELECTION

```
Need to monitor processes?
    |
    ├─ One-time snapshot needed?
    │   └─ Use `ps aux` or `ps -ef`
    │
    ├─ Real-time monitoring needed?
    │   ├─ Basic terminal available?
    │   │   └─ Use `top`
    │   │
    │   └─ Enhanced UI desired?
    │       └─ Use `htop` (if installed)
    │
    └─ Scripting/automation needed?
        └─ Use `ps` with custom format
```

---

## FEATURE COMPARISON MATRIX

| Feature | ps | top | htop |
|---------|----|----|------|
| **Output format options** | Highly customizable (`-o`) | Fixed columns | Interactive column selection |
| **Real-time monitoring** | ❌ Snapshot only | ✅ Updates every 3s | ✅ Updates every 1s |
| **Color output** | ❌ No | ⚠️ Limited | ✅ Full color coding |
| **CSV/JSON export** | ✅ Easy with `-o` | ❌ Difficult | ❌ Not built-in |
| **Filtering capability** | ✅ Powerful (grep, awk) | ⚠️ Basic (`u` for user) | ✅ Interactive filter (F4) |
| **Sorting options** | ✅ `--sort` flag | ✅ Interactive (M, P, T) | ✅ Interactive (F6) |
| **Performance impact** | ⭐ Very low | ⭐⭐ Low | ⭐⭐⭐ Moderate |
| **Memory usage** | ~2MB | ~5MB | ~10MB |
| **Installation required** | ✅ Pre-installed | ✅ Pre-installed | ❌ Needs install |
| **Mouse support** | ❌ No | ❌ No | ✅ Yes |
| **Tree view** | ⚠️ `ps --forest` | ❌ No | ✅ F5 key |
| **Kill processes** | ❌ Use separate `kill` | ✅ `k` key | ✅ F9 key |
| **Search processes** | ✅ Pipe to grep | ❌ No | ✅ F3 key |
| **Scripting friendly** | ✅ Excellent | ❌ Poor | ❌ Poor |

---

## USE CASE SPECIFIC RECOMMENDATIONS

### For Interactive Use
**Winner**: `htop`  
**Reason**: Color-coded, mouse support, easy navigation  
**Example**:
```bash
htop
# Press F2 for setup, F6 to sort, F9 to kill
```

### For Scripting
**Winner**: `ps`  
**Reason**: Consistent output, highly customizable format  
**Example**:
```bash
# Get top 10 CPU consumers in CSV format
ps aux --sort=-%cpu | head -11 | awk '{print $2","$3","$11}'
```

### For Performance Monitoring
**Winner**: `top` (batch mode)  
**Reason**: Real-time, low overhead, universally available  
**Example**:
```bash
# Log top output every 5 seconds
top -b -d 5 -n 12 > top_log.txt
```

### For Debugging
**Winner**: `ps` with custom format  
**Reason**: Precise control over displayed information  
**Example**:
```bash
# Show process tree with full command
ps -ef --forest
# Custom format for debugging
ps -eo pid,ppid,cmd,%mem,%cpu,stat
```

---

## DETAILED COMMAND EXAMPLES

### ps - Snapshot Approach
```bash
# Standard formats
ps aux          # BSD style (most common)
ps -ef          # UNIX style
ps -ely         # Long format with nice values

# Custom output
ps -eo pid,user,%cpu,%mem,cmd --sort=-%cpu | head -10

# Process tree
ps --forest -C nginx

# Specific user
ps -u apache

# Threads
ps -eLf
```

### top - Real-time Monitoring
```bash
# Basic usage
top

# Interactive commands while running:
# M - Sort by memory
# P - Sort by CPU
# k - Kill process
# u - Filter by user
# 1 - Show individual CPUs

# Batch mode for logging
top -b -n 1 > snapshot.txt

# Monitor specific user
top -u nginx
```

### htop - Enhanced Interactive
```bash
# Basic usage
htop

# Interactive features:
# F2 - Setup (customize display)
# F3 - Search
# F4 - Filter
# F5 - Tree view
# F6 - Sort by column
# F9 - Kill process
# F10 - Quit

# Start with tree view
htop -t

# Start with specific user
htop -u nginx
```

---

## HISTORICAL CONTEXT

### Evolution Timeline
1. **1970s**: `ps` created for Unix System V
2. **1984**: `top` introduced for BSD Unix
3. **2004**: `htop` created as modern alternative

### Why Multiple Commands Exist
- **ps**: Original Unix tool, designed for scripting and automation
- **top**: Added real-time monitoring capability
- **htop**: Modern UX improvements (color, mouse, easier navigation)

### Future Direction
- **ps**: Stable, no major changes planned
- **top**: Maintained but not actively developed
- **htop**: Active development, new features added
- **Emerging**: `btop`, `glances` (Python-based)

---

## MIGRATION GUIDES

### From ps to top
```bash
# Old: Get top CPU processes
ps aux --sort=-%cpu | head -10

# New: Real-time top CPU
top -o %CPU
```
**Equivalent output?** No - top is real-time, ps is snapshot

### From top to htop
```bash
# Old: top with user filter
top -u nginx

# New: htop with user filter
htop -u nginx
```
**Equivalent output?** Yes - htop shows same data with better UI

### From top to ps (for scripting)
```bash
# Old: top batch mode
top -b -n 1 | grep nginx

# New: ps with grep
ps aux | grep nginx
```
**Equivalent output?** Similar, but ps is more reliable for scripts

---

## ORGANIZATION STANDARDS

### Recommended Standard: Use All Three
**Why**: Each serves different purposes

### Usage Guidelines

**ps** - Standardize for:
- ✅ Automation scripts
- ✅ Monitoring systems (Nagios, Zabbix)
- ✅ Log analysis
- ✅ CI/CD pipelines

**top** - Standardize for:
- ✅ Quick system checks
- ✅ SSH sessions (always available)
- ✅ Minimal systems (embedded, containers)
- ✅ Performance baselines

**htop** - Standardize for:
- ✅ Interactive troubleshooting
- ✅ Desktop/workstation environments
- ✅ Training new administrators
- ✅ Detailed process analysis

### Training Requirements

| Command | Training Time | Skill Level |
|---------|--------------|-------------|
| ps | 2 hours | Beginner |
| top | 1 hour | Beginner |
| htop | 30 minutes | Beginner |

### Support Considerations
- **ps**: No installation needed, universal support
- **top**: No installation needed, universal support
- **htop**: Requires `yum install htop` or `apt install htop`

---

## QUICK REFERENCE CHEAT SHEET

### Common Tasks Comparison

| Task | ps | top | htop |
|------|----|----|------|
| Find process by name | `ps aux \| grep nginx` | `top` then `o` filter | `F3` search |
| Kill process | `kill $(ps aux \| grep nginx \| awk '{print $2}')` | `k` then PID | `F9` then select |
| Sort by memory | `ps aux --sort=-%mem` | Press `M` | `F6` then select MEM% |
| Show threads | `ps -eLf` | Press `H` | Press `H` |
| Filter by user | `ps -u nginx` | `u` then username | `u` then username |

---

## PERFORMANCE IMPACT COMPARISON

### Resource Usage Test (100 processes)
```bash
# ps - negligible impact
time ps aux > /dev/null
# real: 0.01s, CPU: 0%, Memory: 2MB

# top - low impact
top -b -n 1 > /dev/null
# real: 0.05s, CPU: 1%, Memory: 5MB

# htop - moderate impact
htop --no-color -d 10 > /dev/null
# real: 0.10s, CPU: 2%, Memory: 10MB
```

**Recommendation**: For production monitoring, use `ps` in scripts to minimize overhead.

---

## WHEN TO USE EACH

### Use `ps` when:
- Writing automation scripts
- Need consistent, parseable output
- Minimal system impact required
- Working with legacy systems
- Generating reports

### Use `top` when:
- Quick system health check needed
- SSH into minimal systems
- Real-time monitoring required
- htop not available
- Teaching basic Linux

### Use `htop` when:
- Interactive troubleshooting
- Need visual process tree
- Killing multiple processes
- Detailed CPU/memory analysis
- Training new team members

# Layer 7: Application Layer Troubleshooting

Complete guide to DNS, HTTP/HTTPS, TLS/SSL, and application-level diagnostics.

---

## DNS Troubleshooting

### Basic DNS Testing

```bash
# Quick DNS lookup
host example.com
nslookup example.com
dig example.com +short

# Detailed DNS query
dig example.com

# Test specific DNS server
dig @8.8.8.8 example.com
dig @1.1.1.1 example.com

# Trace DNS resolution path
dig example.com +trace

# Check specific record types
dig example.com A      # IPv4 address
dig example.com AAAA   # IPv6 address
dig example.com MX     # Mail servers
dig example.com NS     # Name servers
dig example.com TXT    # Text records
dig example.com SOA    # Start of authority
```

### DNS Configuration

```bash
# Check DNS configuration
cat /etc/resolv.conf

# systemd-resolved
resolvectl status
systemd-resolve --status

# Test resolution time
time dig example.com

# Flush DNS cache
# systemd-resolved:
resolvectl flush-caches
# nscd:
systemctl restart nscd
# dnsmasq:
systemctl restart dnsmasq
```

### Common DNS Problems

```bash
# Problem 1: No nameserver configured
cat /etc/resolv.conf
# (empty or missing)

# Fix: Add nameserver
echo "nameserver 8.8.8.8" > /etc/resolv.conf
echo "nameserver 1.1.1.1" >> /etc/resolv.conf

# Problem 2: DNS server not responding
dig @8.8.8.8 example.com
# ;; connection timed out; no servers could be reached

# Test connectivity to DNS server
ping -c 2 8.8.8.8
nc -zvu 8.8.8.8 53

# Problem 3: DNSSEC validation failure
dig example.com +dnssec
# Check for validation errors
```

---

## HTTP/HTTPS Troubleshooting

### Basic HTTP Testing

```bash
# Simple GET request
curl http://example.com

# View headers only
curl -I http://example.com

# Verbose output
curl -v http://example.com

# Follow redirects
curl -L http://example.com

# Set custom headers
curl -H "User-Agent: Custom" http://example.com

# POST request
curl -X POST -d "key=value" http://example.com

# Upload file
curl -F "file=@/path/to/file" http://example.com
```

### HTTPS/TLS Testing

```bash
# Test HTTPS connection
curl -v https://example.com

# Check certificate
openssl s_client -connect example.com:443 -servername example.com

# View certificate details
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -text

# Check certificate expiration
echo | openssl s_client -connect example.com:443 2>/dev/null | openssl x509 -noout -dates

# Test specific TLS version
openssl s_client -connect example.com:443 -tls1_2
openssl s_client -connect example.com:443 -tls1_3

# Check supported ciphers
nmap --script ssl-enum-ciphers -p 443 example.com
```

### Performance Timing

```bash
# Detailed timing information
curl -w "\ntime_namelookup: %{time_namelookup}\ntime_connect: %{time_connect}\ntime_appconnect: %{time_appconnect}\ntime_pretransfer: %{time_pretransfer}\ntime_redirect: %{time_redirect}\ntime_starttransfer: %{time_starttransfer}\ntime_total: %{time_total}\n" -o /dev/null -s https://example.com

# Breakdown:
# time_namelookup:    DNS resolution time
# time_connect:       TCP connection time
# time_appconnect:    TLS handshake time
# time_starttransfer: Time to first byte
# time_total:         Total request time
```

### Web Server Diagnostics

```bash
# Check if web server is running
systemctl status nginx
systemctl status apache2
systemctl status httpd

# Check listening ports
ss -tlnp | grep :80
ss -tlnp | grep :443

# Test local connection
curl -I http://localhost
curl -I https://localhost

# Check logs
journalctl -u nginx -f
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Check configuration
nginx -t
apache2ctl configtest
httpd -t
```

---

## Database Connectivity

### MySQL/MariaDB

```bash
# Test connection
mysql -h host -u user -p -e "SELECT 1"

# Check if MySQL is running
systemctl status mysql
systemctl status mariadb

# Check listening port
ss -tlnp | grep :3306

# Test port connectivity
nc -zv db.example.com 3306
telnet db.example.com 3306

# Check connections
mysql -e "SHOW PROCESSLIST"
mysql -e "SHOW STATUS LIKE 'Threads_connected'"

# Check max connections
mysql -e "SHOW VARIABLES LIKE 'max_connections'"
```

### PostgreSQL

```bash
# Test connection
psql -h host -U user -d database -c "SELECT 1"

# Check if PostgreSQL is running
systemctl status postgresql

# Check listening port
ss -tlnp | grep :5432

# Check connections
psql -c "SELECT count(*) FROM pg_stat_activity"

# Check max connections
psql -c "SHOW max_connections"
```

### MongoDB

```bash
# Test connection
mongosh --host host --eval "db.adminCommand('ping')"

# Check if MongoDB is running
systemctl status mongod

# Check listening port
ss -tlnp | grep :27017

# Check connections
mongosh --eval "db.serverStatus().connections"
```

---

## Application-Level Diagnostics

### Service Status

```bash
# Check service status
systemctl status service_name

# View recent logs
journalctl -u service_name -n 50

# Follow logs in real-time
journalctl -u service_name -f

# Check service dependencies
systemctl list-dependencies service_name

# Check failed services
systemctl list-units --state=failed
```

### Process Analysis

```bash
# Find process by name
pgrep -a nginx
ps aux | grep nginx

# Check process resources
top -p $(pgrep nginx | head -1)
htop -p $(pgrep nginx | head -1)

# Check open files
lsof -p PID
lsof -c nginx

# Check network connections
lsof -i -P -n | grep nginx
ss -tnp | grep nginx
```

### Application Logs

```bash
# Common log locations
tail -f /var/log/syslog
tail -f /var/log/messages
tail -f /var/log/application.log

# Search for errors
grep -i error /var/log/application.log
grep -i exception /var/log/application.log

# Count error occurrences
grep -c "ERROR" /var/log/application.log

# Show errors with context
grep -B 5 -A 5 "ERROR" /var/log/application.log
```

---

## Troubleshooting Workflows

### Workflow 1: Website Not Loading

```bash
#!/bin/bash
URL="$1"

echo "=== Troubleshooting $URL ==="

# Extract host and port
HOST=$(echo "$URL" | sed -E 's|https?://([^:/]+).*|\1|')
if [[ "$URL" =~ ^https ]]; then
    PORT=443
else
    PORT=80
fi

# Step 1: DNS resolution
echo -n "DNS resolution: "
if IP=$(dig +short "$HOST" | head -1); then
    echo "✓ $HOST → $IP"
else
    echo "✗ DNS failed"
    echo "→ Check /etc/resolv.conf"
    exit 1
fi

# Step 2: Port connectivity
echo -n "Port $PORT connectivity: "
if nc -zv -w 2 "$IP" "$PORT" 2>&1 | grep -q succeeded; then
    echo "✓ Port reachable"
else
    echo "✗ Port unreachable"
    exit 1
fi

# Step 3: HTTP response
echo -n "HTTP response: "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
if [[ "$STATUS" == "200" ]]; then
    echo "✓ HTTP $STATUS"
elif [[ "$STATUS" =~ ^[45] ]]; then
    echo "⚠️  HTTP $STATUS (client/server error)"
else
    echo "✓ HTTP $STATUS (redirect/other)"
fi

# Step 4: Response time
echo -n "Response time: "
TIME=$(curl -w "%{time_total}" -o /dev/null -s "$URL")
echo "${TIME}s"
```

### Workflow 2: Database Connection Issues

```bash
#!/bin/bash
DB_HOST="$1"
DB_PORT="${2:-3306}"
DB_USER="$3"

echo "=== Database Connectivity Test ==="

# Step 1: Network connectivity
echo -n "Network connectivity: "
if ping -c 2 -W 2 "$DB_HOST" &>/dev/null; then
    echo "✓ Host reachable"
else
    echo "✗ Host unreachable"
    exit 1
fi

# Step 2: Port connectivity
echo -n "Port $DB_PORT: "
if nc -zv -w 2 "$DB_HOST" "$DB_PORT" 2>&1 | grep -q succeeded; then
    echo "✓ Port open"
else
    echo "✗ Port closed/filtered"
    exit 1
fi

# Step 3: Database authentication
echo -n "Database authentication: "
if mysql -h "$DB_HOST" -u "$DB_USER" -p -e "SELECT 1" &>/dev/null; then
    echo "✓ Authentication successful"
else
    echo "✗ Authentication failed"
fi
```

---

## Quick Reference

### DNS Commands

| Task | Command |
|------|---------|
| Basic lookup | `dig example.com +short` |
| Detailed query | `dig example.com` |
| Trace resolution | `dig example.com +trace` |
| Test DNS server | `dig @8.8.8.8 example.com` |
| Check config | `cat /etc/resolv.conf` |
| Flush cache | `resolvectl flush-caches` |

### HTTP/HTTPS Commands

| Task | Command |
|------|---------|
| GET request | `curl http://example.com` |
| View headers | `curl -I http://example.com` |
| Verbose output | `curl -v https://example.com` |
| Check certificate | `openssl s_client -connect host:443` |
| Certificate expiry | `echo \| openssl s_client -connect host:443 \| openssl x509 -noout -dates` |
| Response timing | `curl -w "%{time_total}" -o /dev/null -s URL` |

### Common Issues

| Symptom | Likely Cause | First Check |
|---------|--------------|-------------|
| DNS fails | Wrong nameserver | `cat /etc/resolv.conf` |
| Slow DNS | DNS server issue | `time dig example.com` |
| HTTP 502/503 | Backend down | `systemctl status service` |
| HTTP 404 | Wrong URL/path | Check URL |
| TLS error | Certificate issue | `openssl s_client -connect host:443` |
| DB timeout | Network/firewall | `nc -zv db_host 3306` |

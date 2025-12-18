# Linux Networking Deep Dive for Enterprise

**Level:** Expert / Network Engineer
**Focus:** Kernel Stack, Tuning, Namespaces, and Packet Flow.

---

## 1. TCP/IP Stack Implementation

### 1.1 The Socket Buffer (`sk_buff`)
The core data structure in the Linux networking subsystem.
*   **Role**: holds the packet data and state (headers, device, protocol).
*   **Zero-Copy**: As a packet moves up the stack (Driver -> IP -> TCP), Linux doesn't copy the data. It just moves pointers in the `sk_buff` head/tail.
*   **OOM Risk**: If applications don't read from sockets, `sk_buffs` pile up in kernel memory, potentially causing OOM.

### 1.2 TCP State Machine Issues
*   **TIME_WAIT**:
    *   **Purpose**: Ensures delayed packets from an old connection don't confuse a new one. Host waits 2 * MSL (Max Segment Lifetime) = 60s.
    *   **Issue**: High-churn servers (Nginx reverse proxy) can run out of local ports because 10,000s of sockets are sitting in TIME_WAIT.
*   **CLOSE_WAIT**:
    *   **Meaning**: The remote side closed the connection (sent FIN), but *your application* hasn't closed the socket yet.
    *   **Cause**: Application bug (forgetting to `close()`).

### 1.3 Connection Tracking (Conntrack)
Stateful firewalls (iptables/nftables) must remember connections.
*   **Table**: `/proc/net/nf_conntrack`.
*   **Limit**: `net.netfilter.nf_conntrack_max`.
*   **Symptoms of overflow**: `dmesg` says "nf_conntrack: table full, dropping packet".
*   **Fix**: Increase max or use "NOTRACK" rules for high-volume trusted traffic (e.g., Load Balancer health checks).

### 1.4 NIC Offloading
Modern NICs are smart. They can do work for the CPU.
*   **TSO (TCP Segmentation Offload)**: Application sends a 64KB buffer. OS hands it to NIC. NIC splits it into 1500-byte packets.
*   **LRO (Large Receive Offload)**: NIC merges incoming packets into one big chunk for the CPU.
*   *Warning*: `tcpdump` runs *before* the NIC sends (for TX) and *after* IRQ (for RX). You might see packets larger than MTU in tcpdump. This is normal with TSO/LRO.
*   *Disable if*: You are doing Software Routing/Bridging where packets need to be forwarded exactly as received. `ethtool -K eth0 tso off`.

---

## 2. Kernel Networking Parameters (Sysctl)

Tunables in `/proc/sys/net/ipv4/`.

### 2.1 Connection Management
*   `tcp_fin_timeout` (Def: 60): Time to hold socket in FIN-WAIT-2. Lower to 30s on high-load, dumb web servers.
*   `tcp_keepalive_time` (Def: 7200s): **Two hours** is useless for cloud. Lower to 300s (5m) to detect dead load balancers faster.
*   `ip_local_port_range`: Increase to `1024 65535` if you are an egress proxy.

### 2.2 Syn Floods & Backlog
*   `tcp_max_syn_backlog`: Queue size for half-open (SYN received) connections. Increase for public-facing servers.
*   `somaxconn`: Queue size for ESTABLISHED connections waiting for `accept()`. Application (Listen backlog) must also match this.

### 2.3 TIME_WAIT Mitigation
*   `tcp_tw_reuse = 1`: **Recommended**. Allows reusing TIME_WAIT sockets *if* safe (timestamp checks pass).
*   `tcp_tw_recycle = 0`: **DANGEROUS**. Do not use. Breaks connections from clients behind NAT (shared IP, different timestamps). Removed in newer kernels.

---

## 3. Network Namespaces (Netns)

The foundation of Docker/Kubernetes networking.

### 3.1 Concepts
*   **Isolation**: Each namespace has its own loopback, interfaces, routing table, and iptables rules.
*   **Creation**: `ip netns add blue`.
*   **Execution**: `ip netns exec blue ip addr`.

### 3.2 Connectivity (Veth Pairs)
Virtual Ethernet cables. One end in host, one End in container.
1.  Create pair: `ip link add veth0 type veth peer name veth1`.
2.  Move end: `ip link set veth1 netns blue`.
3.  Bridge: Connect host end (`veth0`) to a bridge (`docker0`) to allow switching.

### 3.3 Bridge vs. Macvlan vs. Ipvlan
*   **Bridge**: Standard Software Switch. Slowest (MAC lookups).
*   **Macvlan**: Light. Sub-interface with its own MAC. Direct wire access.
*   **Ipvlan**: L3/L2 modes. Shares MAC with master. Good for VMs on clouds that block unknown MACs.

---

## 4. Packet Flow Analysis

### 4.1 The Journey (Ingress)
1.  **Wire** -> **NIC** (DMA to RAM).
2.  Hardware Interrupt -> **Driver**.
3.  **GRO/LRO** (Merging).
4.  **IP Layer**: Verification/Routing.
5.  **Netfilter (PreRouting)**: DNAT/Port Forwarding happens here.
6.  **Routing Decision**: Is it for me (Local) or Forwarding?
7.  **Netfilter (Input)**: Firewalls.
8.  **L4 (TCP/UDP)**: Socket Lookup.
9.  **User Space**: Application reads data.

### 4.2 Netfilter Hooks
*   **PREROUTING**: Before routing. DNAT.
*   **INPUT**: Destined for local socket.
*   **FORWARD**: Routing through box.
*   **OUTPUT**: Created locally.
*   **POSTROUTING**: Leaving box. SNAT/Masquerade.

### 4.3 Traffic Control (TC)
*   QoS happens at the Egress (Output) queue usage `tc`.
*   **Shaping**: Slowing down traffic to a rate (Token Bucket Filter).
*   **Policing**: Dropping traffic exceeding rate (Ingress only).

### 4.4 eBPF (Extended Berkeley Packet Filter)
*   **XDP (eXpress Data Path)**: Runs inside the NIC driver *before* `sk_buff` allocation.
*   **Use case**: Dropping DDoS packets at millions/sec.

---

## 5. Troubleshooting Scenarios

### 5.1 Connection Timeout (Connectivity)
*   **Check**: `ping`, `telnet <ip> <port>`.
*   **Trace**: `tcpdump -ni eth0 port 80`.
    *   See SYN out, nothing back? -> Firewall Drop or routing blackhole.
    *   See SYN out, RST back? -> Port closed or rejected.

### 5.2 Bandwidth Saturation
*   **Bandwidth Delay Product (BDP)**: Speed * Latency = Buffer Size needed.
*   **Issue**: If TCP Window Size < BDP, you cannot fill the pipe.
*   **Fix**: Enable window scaling (`net.ipv4.tcp_window_scaling = 1`) and increase buffer max (`net.core.rmem_max`).

### 5.3 SYN Flood Mitigation
*   **Symptoms**: High `SI` (Soft IRQ) CPU usage. `netstat -s | grep -i listen` shows drops.
*   **Mitigation**:
    1.  Enable **SYN Cookies** (`net.ipv4.tcp_syncookies = 1`). Kernel generates sequence number from IP/Port, avoids allocating memory until ACK returns.
    2.  Increase `tcp_max_syn_backlog`.

### 5.4 MTU and Fragmentation
*   **Scenario**: SSH works, but `cat huge_file` hangs. (Interactive ok, bulk fail).
*   **Cause**: **Path MTU Discovery (PMTUD)** failure.
    *   Client sends 1500 byte packet with "Don't Fragment" (DF) bit.
    *   Intermediate router has 1400 MTU (VPN/Tunnel). Drops packet.
    *   Router sends ICMP "Frag Needed".
    *   **Firewall blocks ICMP**. Client never knows, keeps retrying 1500.
*   **Fix**: Allow ICMP Type 3 Code 4. Or use `TCP MSS Clamping` on router (`iptables -j TCPMSS --clamp-mss-to-pmtu`).

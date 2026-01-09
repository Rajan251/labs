# 🏗️ Tier-2 Architecture Network Diagram

## Complete Architecture Overview

```mermaid
graph TB
    subgraph Internet
        Users[Users/Clients]
    end
    
    subgraph "AWS Cloud - Region: us-east-1"
        subgraph "VPC: 10.0.0.0/16"
            IGW[Internet Gateway<br/>tier2-igw]
            
            subgraph "Availability Zone A (us-east-1a)"
                subgraph "Public Subnet 1<br/>10.0.1.0/24"
                    NAT[NAT Gateway<br/>tier2-nat-gw<br/>Elastic IP: x.x.x.x]
                end
                
                subgraph "Private Subnet 1<br/>10.0.3.0/24"
                    EC2_1[EC2 Instance 1<br/>tier2-private-instance-1<br/>Private IP: 10.0.3.x]
                end
            end
            
            subgraph "Availability Zone B (us-east-1b)"
                subgraph "Public Subnet 2<br/>10.0.2.0/24"
                    PUB2[Reserved for<br/>future resources]
                end
                
                subgraph "Private Subnet 2<br/>10.0.4.0/24"
                    EC2_2[EC2 Instance 2<br/>tier2-private-instance-2<br/>Private IP: 10.0.4.x]
                end
            end
            
            VPN[Client VPN Endpoint<br/>tier2-vpn-endpoint<br/>Client CIDR: 172.16.0.0/22]
            
            SG[Security Group<br/>tier2-ec2-sg<br/>SSH: 10.0.0.0/16<br/>HTTP/HTTPS: 0.0.0.0/0]
        end
    end
    
    VPNClient[VPN Client<br/>AWS VPN Client<br/>IP: 172.16.0.x]
    
    Users -->|HTTPS/443| IGW
    IGW -->|Public Traffic| NAT
    NAT -->|Outbound Internet| EC2_1
    NAT -->|Outbound Internet| EC2_2
    
    VPNClient -.->|VPN Tunnel| VPN
    VPN -.->|SSH Access| EC2_1
    VPN -.->|SSH Access| EC2_2
    
    SG -.->|Firewall Rules| EC2_1
    SG -.->|Firewall Rules| EC2_2
    
    style IGW fill:#ff9900
    style NAT fill:#ff9900
    style VPN fill:#00a1c9
    style EC2_1 fill:#ec7211
    style EC2_2 fill:#ec7211
    style SG fill:#dd344c
```

---

## Traffic Flow Diagrams

### Outbound Internet Traffic (Private Instances → Internet)

```mermaid
sequenceDiagram
    participant EC2 as EC2 Instance<br/>(Private Subnet)
    participant RT as Private Route Table
    participant NAT as NAT Gateway<br/>(Public Subnet)
    participant IGW as Internet Gateway
    participant Internet as Internet
    
    EC2->>RT: Request to 8.8.8.8
    RT->>NAT: Route via 0.0.0.0/0 → NAT
    NAT->>IGW: NAT translation<br/>(Source: Elastic IP)
    IGW->>Internet: Forward request
    Internet->>IGW: Response
    IGW->>NAT: Return traffic
    NAT->>EC2: NAT translation<br/>(Dest: Private IP)
```

---

### VPN Access Flow (User → Private Instance)

```mermaid
sequenceDiagram
    participant User as User's Computer
    participant VPNClient as AWS VPN Client
    participant VPNEndpoint as Client VPN Endpoint
    participant EC2 as EC2 Instance<br/>(Private Subnet)
    
    User->>VPNClient: Connect to VPN
    VPNClient->>VPNEndpoint: TLS Handshake<br/>(Mutual Auth)
    VPNEndpoint->>VPNClient: Assign IP: 172.16.0.x
    VPNClient->>User: Connected
    
    User->>VPNClient: SSH to 10.0.3.x
    VPNClient->>VPNEndpoint: Encrypted tunnel
    VPNEndpoint->>EC2: Route to private IP
    EC2->>VPNEndpoint: SSH response
    VPNEndpoint->>VPNClient: Encrypted tunnel
    VPNClient->>User: SSH session established
```

---

## Network Topology

### Subnet Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│                        VPC: 10.0.0.0/16                             │
│                     (65,536 IP addresses)                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    PUBLIC TIER                             │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │                                                            │    │
│  │  ┌──────────────────────┐    ┌──────────────────────┐    │    │
│  │  │ Public Subnet 1      │    │ Public Subnet 2      │    │    │
│  │  │ 10.0.1.0/24          │    │ 10.0.2.0/24          │    │    │
│  │  │ AZ: us-east-1a       │    │ AZ: us-east-1b       │    │    │
│  │  │ IPs: 251 usable      │    │ IPs: 251 usable      │    │    │
│  │  │                      │    │                      │    │    │
│  │  │ ┌──────────────────┐ │    │                      │    │    │
│  │  │ │ NAT Gateway      │ │    │                      │    │    │
│  │  │ │ + Elastic IP     │ │    │                      │    │    │
│  │  │ └──────────────────┘ │    │                      │    │    │
│  │  └──────────────────────┘    └──────────────────────┘    │    │
│  │                                                            │    │
│  │  Route Table: tier2-public-rt                             │    │
│  │  • 10.0.0.0/16 → local                                    │    │
│  │  • 0.0.0.0/0 → Internet Gateway                           │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    PRIVATE TIER                            │    │
│  ├────────────────────────────────────────────────────────────┤    │
│  │                                                            │    │
│  │  ┌──────────────────────┐    ┌──────────────────────┐    │    │
│  │  │ Private Subnet 1     │    │ Private Subnet 2     │    │    │
│  │  │ 10.0.3.0/24          │    │ 10.0.4.0/24          │    │    │
│  │  │ AZ: us-east-1a       │    │ AZ: us-east-1b       │    │    │
│  │  │ IPs: 251 usable      │    │ IPs: 251 usable      │    │    │
│  │  │                      │    │                      │    │    │
│  │  │ ┌──────────────────┐ │    │ ┌──────────────────┐ │    │    │
│  │  │ │ EC2 Instance 1   │ │    │ │ EC2 Instance 2   │ │    │    │
│  │  │ │ Private IP only  │ │    │ │ Private IP only  │ │    │    │
│  │  │ └──────────────────┘ │    │ └──────────────────┘ │    │    │
│  │  └──────────────────────┘    └──────────────────────┘    │    │
│  │                                                            │    │
│  │  Route Table: tier2-private-rt                            │    │
│  │  • 10.0.0.0/16 → local                                    │    │
│  │  • 0.0.0.0/0 → NAT Gateway                                │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

```mermaid
graph LR
    subgraph "Security Layers"
        A[Internet] -->|HTTPS/443| B[Internet Gateway]
        B --> C[Public Subnet<br/>NAT Gateway]
        C -->|Filtered| D[Private Subnet<br/>EC2 Instances]
        
        E[VPN Client] -.->|Encrypted<br/>Tunnel| F[Client VPN<br/>Endpoint]
        F -.->|Authorized<br/>Access| D
        
        G[Security Group<br/>tier2-ec2-sg] -.->|Firewall<br/>Rules| D
        H[Network ACL<br/>Default] -.->|Subnet<br/>Level| C
        H -.->|Subnet<br/>Level| D
    end
    
    style A fill:#ff6b6b
    style B fill:#ff9900
    style C fill:#ffd93d
    style D fill:#6bcf7f
    style E fill:#4d96ff
    style F fill:#00a1c9
    style G fill:#dd344c
    style H fill:#a29bfe
```

---

## IP Address Allocation

| CIDR Block | Network | First IP | Last IP | Usable IPs | Purpose |
|------------|---------|----------|---------|------------|---------|
| **10.0.0.0/16** | 10.0.0.0 | 10.0.0.1 | 10.0.255.254 | 65,534 | **VPC** |
| 10.0.1.0/24 | 10.0.1.0 | 10.0.1.1 | 10.0.1.254 | 251 | Public Subnet 1 (AZ-a) |
| 10.0.2.0/24 | 10.0.2.0 | 10.0.2.1 | 10.0.2.254 | 251 | Public Subnet 2 (AZ-b) |
| 10.0.3.0/24 | 10.0.3.0 | 10.0.3.1 | 10.0.3.254 | 251 | Private Subnet 1 (AZ-a) |
| 10.0.4.0/24 | 10.0.4.0 | 10.0.4.1 | 10.0.4.254 | 251 | Private Subnet 2 (AZ-b) |
| **172.16.0.0/22** | 172.16.0.0 | 172.16.0.1 | 172.16.3.254 | 1,022 | **VPN Clients** |

### Reserved IPs (AWS)
Each subnet reserves 5 IPs:
- `.0` - Network address
- `.1` - VPC router
- `.2` - DNS server
- `.3` - Future use
- `.255` - Broadcast address

---

## High Availability Design

```mermaid
graph TB
    subgraph "Multi-AZ Deployment"
        subgraph "AZ-A (us-east-1a)"
            PS1[Public Subnet 1<br/>10.0.1.0/24]
            PRS1[Private Subnet 1<br/>10.0.3.0/24]
            NAT1[NAT Gateway]
            EC2_A[EC2 Instance 1]
            
            PS1 --> NAT1
            NAT1 --> PRS1
            PRS1 --> EC2_A
        end
        
        subgraph "AZ-B (us-east-1b)"
            PS2[Public Subnet 2<br/>10.0.2.0/24]
            PRS2[Private Subnet 2<br/>10.0.4.0/24]
            EC2_B[EC2 Instance 2]
            
            PS2 --> PRS2
            PRS2 --> EC2_B
        end
        
        IGW[Internet Gateway<br/>Highly Available]
        
        IGW --> PS1
        IGW --> PS2
    end
    
    style AZ-A fill:#e3f2fd
    style AZ-B fill:#fff3e0
    style IGW fill:#ff9900
    style NAT1 fill:#ff9900
```

**HA Features**:
- ✅ Resources distributed across 2 AZs
- ✅ Internet Gateway is inherently HA
- ⚠️ Single NAT Gateway (cost optimization)
- 💡 For production: Add NAT Gateway in AZ-B

---

## Cost Breakdown

```mermaid
pie title Monthly Cost Distribution (~$203)
    "Client VPN Endpoint" : 72
    "VPN Connections (2)" : 72
    "NAT Gateway" : 32
    "NAT Data Transfer" : 4.5
    "EC2 Instances (2)" : 15
    "EBS Storage" : 4
    "Elastic IP" : 3.6
```

---

**Return to**: [Main README](../README.md) | [Quick Reference](../QUICK_REFERENCE.md)

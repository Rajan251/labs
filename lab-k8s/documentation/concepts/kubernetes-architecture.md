# Kubernetes Architecture Deep Dive

This document provides a visual and detailed explanation of the Kubernetes architecture, illustrating how the Control Plane and Worker Nodes interact to manage containerized applications.

## High-Level Architecture

Kubernetes follows a client-server architecture with a **Control Plane** (Master) and **Worker Nodes**.

```mermaid
graph TB
    subgraph "Control Plane (Master Node)"
        API[API Server]
        SCH[Scheduler]
        CM[Controller Manager]
        ETCD[(etcd)]
        CCM[Cloud Controller Manager]
    end

    subgraph "Worker Node 1"
        K1[Kubelet]
        P1[Kube-Proxy]
        CR1[Container Runtime]
        subgraph "Pods 1"
            Pod1[Pod A]
            Pod2[Pod B]
        end
    end

    subgraph "Worker Node 2"
        K2[Kubelet]
        P2[Kube-Proxy]
        CR2[Container Runtime]
        subgraph "Pods 2"
            Pod3[Pod C]
        end
    end

    %% Connections
    User[User / kubectl] --> API
    API <--> ETCD
    API <--> SCH
    API <--> CM
    API <--> CCM
    
    API <--> K1
    API <--> K2
    
    K1 --> CR1
    K2 --> CR2
    
    classDef master fill:#e1f5fe,stroke:#01579b,stroke-width:2px;
    classDef worker fill:#f3e5f5,stroke:#4a148c,stroke-width:2px;
    classDef component fill:#ffffff,stroke:#333,stroke-width:1px;
    
    class API,SCH,CM,ETCD,CCM master;
    class K1,P1,CR1,K2,P2,CR2 worker;
    class Pod1,Pod2,Pod3 component;
```

## Component Breakdown

### 1. Control Plane Components

The Control Plane makes global decisions about the cluster (e.g., scheduling) and detects/responds to cluster events.

| Component | Description |
|-----------|-------------|
| **kube-apiserver** | The front end of the Kubernetes control plane. It exposes the Kubernetes API and validates/configures data for API objects (pods, services, etc.). |
| **etcd** | Consistent and highly-available key value store used as Kubernetes' backing store for all cluster data. |
| **kube-scheduler** | Watches for newly created Pods with no assigned node, and selects a node for them to run on based on resource requirements, constraints, and affinity specifications. |
| **kube-controller-manager** | Runs controller processes (e.g., Node Controller, Job Controller, EndpointSlice Controller) that regulate the state of the system. |
| **cloud-controller-manager** | Embeds cloud-specific control logic. It lets you link your cluster into your cloud provider's API. |

### 2. Worker Node Components

Worker nodes maintain running pods and provide the Kubernetes runtime environment.

| Component | Description |
|-----------|-------------|
| **kubelet** | An agent that runs on each node. It ensures that containers are running in a Pod. It takes a set of PodSpecs and ensures that the containers described in those PodSpecs are running and healthy. |
| **kube-proxy** | A network proxy that runs on each node. It maintains network rules on nodes, allowing network communication to your Pods from network sessions inside or outside of your cluster. |
| **Container Runtime** | The software that is responsible for running containers (e.g., containerd, CRI-O, Docker Engine). |

## Pod Creation Flow

Understanding how a Pod gets scheduled and started is crucial for debugging.

```mermaid
sequenceDiagram
    participant User
    participant API as API Server
    participant ETCD as etcd
    participant SCH as Scheduler
    participant Kubelet as Kubelet (Node)
    participant CRI as Container Runtime

    User->>API: kubectl apply -f pod.yaml
    API->>API: Validate Request
    API->>ETCD: Persist Pod Object (Pending)
    ETCD-->>API: Confirmed
    API-->>User: Pod Created

    loop Watch Loop
        SCH->>API: Watch for Unscheduled Pods
        API-->>SCH: New Pod Found
    end

    SCH->>SCH: Filter & Score Nodes
    SCH->>API: Bind Pod to Node X
    API->>ETCD: Update Pod Status (Assigned)
    ETCD-->>API: Confirmed

    loop Watch Loop
        Kubelet->>API: Watch for Pods on Node X
        API-->>Kubelet: New Pod Assignment
    end

    Kubelet->>CRI: Pull Image
    CRI-->>Kubelet: Image Pulled
    Kubelet->>CRI: Create & Start Container
    CRI-->>Kubelet: Container Started
    Kubelet->>API: Update Pod Status (Running)
    API->>ETCD: Persist Status
```

### Flow Description

1.  **Submission**: User submits a Pod spec to the API Server.
2.  **Persistence**: API Server writes the Pod object to `etcd`.
3.  **Scheduling**: The Scheduler notices a Pod with no `nodeName` set. It evaluates all nodes and selects the best fit.
4.  **Binding**: The Scheduler tells the API Server to bind the Pod to a specific Node.
5.  **Execution**: The Kubelet on the target Node notices the new assignment.
6.  **Runtime**: Kubelet instructs the Container Runtime (CRI) to pull the image and start the container.
7.  **Status Update**: Kubelet reports the status back to the API Server.

## Networking Architecture

How Pods communicate within the cluster.

```mermaid
graph LR
    subgraph "Node 1"
        P1[Pod 1 (10.244.1.2)]
        P2[Pod 2 (10.244.1.3)]
        BR1[cni0 Bridge]
        P1 --- BR1
        P2 --- BR1
    end

    subgraph "Node 2"
        P3[Pod 3 (10.244.2.2)]
        BR2[cni0 Bridge]
        P3 --- BR2
    end

    BR1 --- ETH1[eth0]
    BR2 --- ETH2[eth0]
    
    ETH1 --- NET[Cluster Network / CNI Overlay]
    ETH2 --- NET

    style NET fill:#f9f,stroke:#333,stroke-width:2px
```

### Key Networking Rules
1.  **Pod-to-Pod**: All Pods can communicate with all other Pods without NAT.
2.  **Node-to-Pod**: All Nodes can communicate with all Pods without NAT.
3.  **IP-per-Pod**: Every Pod gets its own IP address.

## Summary

This architecture ensures high availability, scalability, and loose coupling between components. The **Control Plane** manages the desired state, while **Worker Nodes** tirelessly work to match the actual state to the desired state.

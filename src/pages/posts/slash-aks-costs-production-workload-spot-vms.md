---
layout: ../../layouts/post.astro
title: "Slash Your AKS Costs: Run Resilient Production Workloads on Azure Spot VMs"
pubDate: 2025-06-06
description: "Learn how to implement intelligent failover and failback mechanisms for Azure Spot VMs in production AKS environments, achieving up to 90% cost savings while maintaining high availability through automated orchestration between spot and on-demand resources."
author: "Torstein Skulbru"
isPinned: true
excerpt: "Azure Spot VMs offer up to 90% cost savings, but production adoption brings complex challenges beyond basic setup. This guide tackles the real problems teams face: automatic failover during spot evictions, intelligent failback when capacity returns, and seamless orchestration between spot and on-demand resources. We'll explore how to combine AKS features, Kubernetes best practices, and tools like the descheduler to build a resilient system that maximizes cost savings without sacrificing reliability."
blueskyUri: "at://did:plc:rmnykyqh3zleost7ii4qe5nc/app.bsky.feed.post/3lqwaglsecc2j"
image:
  src: "/images/slash-aks-containers.jpg"
  alt: "Stacked containers"
tags: ["azure", "kubernetes", "aks", "spot-vms", "devops"]
---

Cloud computing offers incredible scalability, but costs can quickly escalate. For organizations leveraging Azure Kubernetes Service (AKS), one powerful strategy to significantly reduce compute expenses without compromising reliability is by utilizing Azure Spot Virtual Machines. Spot VMs provide access to Azure's unused compute capacity at substantial discounts compared to pay-as-you-go prices.

However, the journey to production-ready Spot VM adoption isn't without its challenges. Like many teams, we wanted to move our production services over to Spot VMs as much as possible to cut costs. But the reality of Spot VMs quickly became apparent: they can be evicted, and depending on which machine type you select when creating the node pool, eviction rates can be quite high—many have 20% or higher eviction rates. Even more concerning, you risk having your entire pool evicted at once.

The initial challenge seems straightforward: if your deployment configuration isn't set up to offload to non-spot pools during spot downtime, you'll experience actual downtime. But having deployment pods moved to non-spot pools when spot pools aren't available is just part of the problem. The real complexity emerges when the spot pool comes back online—how do you move the deployment pods back into the spot pool to maintain your cost savings?

And then there's the cluster autoscaler puzzle: how do you ensure your pods are actually triggering the autoscaler to scale the newly restored spot pool so that everything gets moved back efficiently? These are the exact challenges I've struggled with in production environments.

This guide will walk you through the complete solution—from configuring your AKS clusters to harness the cost benefits of Spot VMs, to implementing intelligent failover and failback mechanisms that ensure high availability during spot pool fluctuations. We'll explore how to combine AKS features, Kubernetes best practices, and tools like the `descheduler` to build a resilient system that automatically handles the complex dance between spot and on-demand resources, ensuring you get maximum cost savings without sacrificing reliability.

## Understanding Azure Spot VMs

Azure Spot VMs offer up to 90% cost savings by providing access to Azure's unused compute capacity. However, they come with the trade-off that Azure can reclaim them when capacity is needed for on-demand workloads.

For a comprehensive understanding of Azure Spot VMs, including workload suitability, setup instructions, and basic configuration patterns, check out our detailed guide: [Azure Spot VMs in AKS: Complete Guide to Cost-Effective Kubernetes Workloads](/posts/azure-spot-vms-aks-guide).

This article focuses on the advanced challenges of running production workloads on spot instances—specifically the complex problems of automatic failover and failback that most teams encounter when trying to maximize cost savings while maintaining reliability.

## The Real Challenge: Intelligent Failover and Failback

While setting up basic spot node pools is straightforward, the real complexity emerges in production scenarios where you need:

1. **Automatic failover** when spot capacity becomes unavailable
2. **Intelligent failback** when spot capacity returns
3. **Seamless orchestration** between spot and on-demand resources
4. **Cost optimization** without sacrificing reliability

The challenge isn't just moving workloads off spot nodes during evictions—it's ensuring they automatically return to spot nodes when capacity becomes available again, and doing so in a way that triggers the cluster autoscaler appropriately.

## Implementation Overview

This guide will walk you through implementing the following components to create a production-ready spot VM architecture:

### Helm Charts to Install

#### AKS Node Termination Handler

- **Chart**: `aks-node-termination-handler`
- **Purpose**: Responsible for shutting down applications if node or pools are shutdown or becomes unavailable
- **Repository**: `https://maksim-paskal.github.io/aks-node-termination-handler/`

#### Cluster Overprovisioner

- **Chart**: `deliveryhero/cluster-overprovisioner`
- **Purpose**: Creates low-priority placeholder pods that provide instant failover capacity
- **Repository**: `https://charts.deliveryhero.io/`

#### Kubernetes Descheduler

- **Chart**: `descheduler/descheduler`
- **Purpose**: Evicts pods from suboptimal nodes to enable intelligent failback to spot nodes
- **Repository**: `https://kubernetes-sigs.github.io/descheduler/`

### Kubernetes Resources to Configure

- `cluster-autoscaler-priority-expander` - Defines node pool priority for cost optimization
- Application deployments with spot node affinity and anti-affinity rules
- Pod Disruption Budgets (PDBs): Service availability protection during node drains and evictions


### Azure CLI Commands

#### Cluster Autoscaler Configuration

- Update AKS cluster to use priority expander strategy
- Configure node pool scaling parameters

#### Node Pool Management

- Spot node pool configuration and scaling limits
- On-demand node pool setup for failover capacity

## Prerequisites

Before implementing advanced Spot VM strategies, ensure you have:

- An operational AKS cluster with cluster autoscaler enabled
- Two user node pools: one Spot pool (e.g., `worker-spot-pool`) and one on-demand pool (e.g., `worker-on-demand-pool`)
- Appropriate RBAC permissions to modify cluster autoscaler configuration

## Cluster Autoscaler Priority Configuration

To maximize cost savings, configure the Cluster Autoscaler to prefer Spot node pools over more expensive on-demand pools using the `priority` expander strategy.

First, update your AKS cluster to use the priority expander:

```bash
az aks update -g myResourceGroup -n myAKSCluster --cluster-autoscaler-profile expander=priority
```

Next, create a ConfigMap that defines the priority order. **The ConfigMap name must be exactly as shown below:**

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cluster-autoscaler-priority-expander
  namespace: kube-system
data:
  priorities: |-
    20:
    - .*spot.*
    10:
    - .*
```

This configuration instructs the Cluster Autoscaler to:

1. **First priority (20)**: Scale up any node pool with "spot" in its name
2. **Second priority (10)**: Fall back to any other node pool if Spot capacity is unavailable

AKS automatically tags nodes in Spot node pools with `kubernetes.azure.com/scalesetpriority: spot`, enabling the regex pattern matching. With this setup, your workloads will automatically benefit from Spot pricing when capacity is available, with seamless fallback to on-demand instances when needed.

## Node Termination Handling

Azure Spot VMs can be evicted with a 30-second notice when Azure needs the capacity back. To handle these evictions gracefully, we need to ensure pods are properly drained from nodes before termination.

### Termination Grace Period

Configure appropriate `terminationGracePeriodSeconds` in your pod specifications to allow applications time to shut down cleanly:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      terminationGracePeriodSeconds: 60  # Allow 60 seconds for graceful shutdown
      containers:
      - name: my-app
        # ... container spec
```

### AKS Node Termination Handler

For production environments, consider implementing the [AKS Node Termination Handler](https://github.com/Azure/aks-node-termination-handler) to proactively drain nodes when eviction notices are received. This handler monitors Azure's scheduled events and initiates pod eviction before the node is forcibly terminated.

## Pod Affinity and Anti-Affinity Rules

Affinity rules are crucial for distributing workloads across failure domains, minimizing the impact of simultaneous Spot VM evictions. Use `podAntiAffinity` to spread replicas strategically:

### Distribution Strategies

- **Across Availability Zones**: Use `topology.kubernetes.io/zone` to distribute pods across different zones
- **Across Nodes**: Use `kubernetes.io/hostname` to ensure replicas don't colocate on the same node
- **Across Node Pools**: Use node pool labels to spread across different VM series

### Example Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-critical-app
spec:
  replicas: 3
  template:
    spec:
      affinity:
        nodeAffinity:
          # Prefer Spot nodes but allow on-demand as fallback
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: kubernetes.azure.com/scalesetpriority
                operator: In
                values:
                - spot
        podAntiAffinity:
          # Strongly prefer spreading across zones
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - my-critical-app
              topologyKey: topology.kubernetes.io/zone
          # Secondary preference: spread across nodes
          - weight: 50
            podAffinityTerm:
              labelSelector:
                matchExpressions:
                - key: app
                  operator: In
                  values:
                  - my-critical-app
              topologyKey: kubernetes.io/hostname
      tolerations:
      # Allow scheduling on Spot nodes
      - key: "kubernetes.azure.com/scalesetpriority"
        operator: "Equal"
        value: "spot"
        effect: "NoSchedule"
```

## Pod Disruption Budgets

Pod Disruption Budgets (PDBs) limit the number of pods that can be simultaneously evicted, preventing service outages during node drains. This is essential when multiple Spot nodes are evicted simultaneously.

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-critical-app-pdb
spec:
  minAvailable: 2  # Ensure at least 2 pods remain available
  selector:
    matchLabels:
      app: my-critical-app
```

Alternative configuration using percentage:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: my-critical-app-pdb
spec:
  maxUnavailable: 25%  # Allow up to 25% of pods to be unavailable
  selector:
    matchLabels:
      app: my-critical-app
```

PDBs work with the eviction API to ensure that when nodes are drained (either due to Spot evictions or maintenance), your services maintain minimum availability requirements.

## Cluster Overprovisioning for Instant Failover

When Spot nodes are evicted, evicted pods need somewhere to land immediately. Cluster overprovisioning creates "headroom" by running low-priority placeholder pods that can be quickly evicted to make room for your critical workloads.

### Implementation with Helm

Use the [cluster-overprovisioner](https://github.com/deliveryhero/helm-charts/tree/master/stable/cluster-overprovisioner) Helm chart:

```bash
helm repo add deliveryhero https://charts.deliveryhero.io/
helm install cluster-overprovisioner deliveryhero/cluster-overprovisioner -f overprovisioner-values.yaml
```

### Configuration Example

```yaml
# overprovisioner-values.yaml
fullnameOverride: "overprovision"

deployments:
- name: spot
  replicaCount: 1
  resources:
    requests:
      cpu: 2      # Reserve 1 CPU core
      memory: 4Gi     # Reserve 2GB memory
  nodeSelector:
    kubernetes.azure.com/scalesetpriority: spot
  tolerations:
  - key: "kubernetes.azure.com/scalesetpriority"
    operator: "Equal"
    value: "spot"
    effect: "NoSchedule"
```

### How It Works

1. **Placeholder pods** run with very low priority, consuming resources but doing nothing
2. **When Spot eviction occurs**, critical pods are scheduled and evict the placeholder pods
3. **Placeholder pods become pending**, triggering cluster autoscaler to add new nodes
4. **Critical workloads get immediate placement** instead of waiting for new nodes

### (Optional) Dynamic Scaling with Cluster Proportional Autoscaler

For environments with varying cluster sizes, automatically scale overprovisioning based on the number of Spot nodes:

```bash
# Install cluster-proportional-autoscaler
kubectl apply -f https://github.com/kubernetes-sigs/cluster-proportional-autoscaler/releases/latest/download/cluster-proportional-autoscaler.yaml
```

Configure it to scale overprovisioning pods:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: overprovision-scaler
  namespace: kube-system
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: autoscaler
        image: registry.k8s.io/cpa/cluster-proportional-autoscaler:1.8.8
        command:
        - /cluster-proportional-autoscaler
        - --namespace=default
        - --configmap=overprovision-config
        - --target=deployment/overprovision-spot
        - --nodelabels=kubernetes.azure.com/scalesetpriority=spot
        - --logtostderr=true
        - --v=2
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: overprovision-config
  namespace: default
data:
  linear: |-
    {
      "coresPerReplica": 4,
      "nodesPerReplica": 1,
      "preventSinglePointFailure": true,
      "includeUnschedulableNodes": true
    }
```

This configuration creates one overprovisioning pod for every 4 CPU cores of Spot nodes, ensuring proportional headroom as your cluster scales.

## Intelligent Failback with Kubernetes Descheduler

While the Cluster Autoscaler Priority Expander ensures new workloads prefer spot nodes, it doesn't automatically move existing pods from on-demand nodes back to spot nodes when spot capacity becomes available again. This is where the [Kubernetes Descheduler](https://github.com/kubernetes-sigs/descheduler) becomes essential.

The Descheduler is a Kubernetes component that identifies and evicts pods that are running on suboptimal nodes based on configurable policies. In our spot VM architecture, it serves as the intelligent failback mechanism that moves workloads from expensive on-demand nodes back to cost-effective spot nodes when capacity returns.

### How Descheduler Enables Cost Optimization

When spot nodes become available again after an eviction event, your workloads may still be running on more expensive on-demand nodes. The Descheduler continuously monitors the cluster and identifies pods that violate node affinity preferences—specifically, pods that prefer spot nodes but are currently running on on-demand nodes.

By evicting these pods, the Descheduler forces the Kubernetes scheduler to re-evaluate their placement according to their affinity rules, which will prefer the newly available spot nodes. Combined with cluster overprovisioning, this creates a cascading effect:

1. **Descheduler evicts pods** from on-demand nodes that prefer spot nodes
2. **Evicted pods get rescheduled** to available spot node capacity
3. **If spot capacity is insufficient**, pods land on overprovisioning placeholder pods
4. **Placeholder pods become pending**, triggering cluster autoscaler to add more spot nodes
5. **Process continues** until optimal cost distribution is achieved

### Installation and Configuration

Install the Descheduler using Helm:

```bash
helm repo add descheduler https://kubernetes-sigs.github.io/descheduler/
helm install descheduler descheduler/descheduler --namespace kube-system -f descheduler-values.yaml --set kind=Deployment
```

### Descheduler Configuration for Spot Failback

Create a values file (`descheduler-values.yaml`) that configures the Descheduler to run on spot nodes and target pods violating node affinity preferences:

```yaml
deschedulerPolicyAPIVersion: "descheduler/v1alpha2"

kind: Deployment

# Run descheduler itself on spot nodes to save costs
tolerations:
- key: "kubernetes.azure.com/scalesetpriority"
  operator: "Equal"
  value: "spot"
  effect: "NoSchedule"

deschedulerPolicy:
  profiles:
    - name: nodeAffinity-profile
      pluginConfig:
      - args:
          nodeAffinityType:
          - preferredDuringSchedulingIgnoredDuringExecution
        name: RemovePodsViolatingNodeAffinity
      - args:
          evictLocalStoragePods: true
        name: DefaultEvictor
      plugins:
        deschedule:
          enabled:
          - RemovePodsViolatingNodeAffinity
```

### Key Configuration Explained

#### RemovePodsViolatingNodeAffinity Plugin

- Identifies pods that violate their node affinity preferences
- Targets pods with `preferredDuringSchedulingIgnoredDuringExecution` affinity rules
- Perfect for moving workloads back to preferred spot nodes

#### DefaultEvictor Configuration

- `evictLocalStoragePods: true` allows eviction of pods with local storage
- Ensures comprehensive coverage of workloads that can be safely moved

#### Descheduler Placement

- Runs on spot nodes to practice what it preaches about cost optimization
- Uses tolerations to handle spot node taints
- Includes node affinity to prefer spot nodes for its own placement

### Monitoring Descheduler Activity

The Descheduler provides metrics to monitor its effectiveness:

```bash
# Check descheduler logs
kubectl logs -n kube-system deployment/descheduler

# Monitor pod evictions
kubectl get events --field-selector reason=Evicted
```

Key metrics to watch:

- **pods_evicted**: Total number of pods evicted by the descheduler
- **descheduler_loop_duration_seconds**: Time taken for each descheduling cycle
- **descheduler_strategy_duration_seconds**: Time taken for each strategy execution

### Integration with Overprovisioning: The Critical Missing Piece

The Descheduler works synergistically with cluster overprovisioning, and this integration is absolutely essential for the system to function properly. Here's why overprovisioning is the final missing piece of the puzzle:

**Without Overprovisioning - The Infinite Loop Problem:**

1. Descheduler evicts a pod from an on-demand node
2. No spot node capacity is available (cluster needs to scale)
3. Pod gets rescheduled back to the same on-demand node it was evicted from
4. Descheduler detects the violation again and evicts the pod
5. Process repeats infinitely - no progress is made

**With Overprovisioning - The Solution:**

1. **Descheduler evicts pods** from on-demand nodes
2. **Evicted pods compete** with overprovisioning pods for spot node capacity
3. **If spot capacity is full**, evicted pods displace overprovisioning pods
4. **Displaced overprovisioning pods** become pending, triggering autoscaler
5. **New spot nodes are added**, providing capacity for both workloads and overprovisioning

The key insight is that the Descheduler itself doesn't trigger autoscaling events - it only evicts pods. Without overprovisioning to create the necessary "landing space" and trigger scaling, the Descheduler would be stuck in an endless eviction-reschedule loop, making no actual progress toward cost optimization.

This creates a self-regulating system that automatically optimizes cost distribution while maintaining the safety net of overprovisioning.

## Wrapping Up: Making Spot VMs Work for You

Let’s be real—cloud bills can get out of hand fast, especially when you’re running production workloads. But with a little bit of Kubernetes magic and some clever Azure features, you can seriously cut costs without losing sleep over reliability.

Here’s a quick, friendly recap of how all the moving parts come together:

### The Main Ingredients

- **AKS with Cluster Autoscaler**  
  Your cluster grows and shrinks as needed, so you’re not paying for idle machines.

- **Azure Spot VMs**  
  Super affordable compute power—just remember, Azure can take them back at any time. Great for saving money if you’re ready for a little unpredictability.

- **Separate Node Pools (Spot + On-Demand)**  
  Keep your spot and regular nodes in their own groups. This way, you can control where your apps run and always have a backup plan.

### The Secret Sauce

- **Cluster Autoscaler Priority Expander**  
  Tells Kubernetes to always try the cheap spot nodes first, and only use the pricier on-demand nodes if it has to.

- **Node Affinity & Anti-Affinity**  
  Spreads your apps out so a single spot node going down doesn’t take everything with it.

- **Pod Disruption Budgets (PDBs)**  
  Makes sure not too many pods get evicted at once, so your service stays up.

- **Cluster Overprovisioning**  
  Runs “placeholder” pods to keep some space free. When spot nodes vanish, your real apps can jump in right away.

- **Cluster Proportional Autoscaler**  
  Adjusts the number of placeholder pods as your cluster changes size, so you always have just enough wiggle room.

- **Kubernetes Descheduler**  
  When spot nodes come back, this little helper moves your apps back to the cheaper nodes—so you keep saving.

- **AKS Node Termination Handler**  
  Gives your apps a heads-up before a spot node is evicted, so they can shut down gracefully (no more “surprise, you’re gone!”).

### Why Bother?

- **Automatic Failover:**  
  Spot nodes disappear? No problem—your apps move to on-demand nodes, all on their own.

- **Smart Failback:**  
  Spot nodes return? Your apps slide back over, and your wallet thanks you.

- **Always Chasing the Best Price:**  
  The whole setup is like a self-driving car for your cloud costs—always steering you toward the cheapest, safest route.

---

With this setup, you get the best of both worlds: big savings from spot VMs and the peace of mind that your production workloads are safe. It takes a bit of tinkering to get right, but once it’s humming, your cluster will handle the hard work for you. More savings, less stress—what’s not to love?

Happy hacking, and may your cloud bills always be tiny!
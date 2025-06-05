---
layout: ../../layouts/post.astro
title: "Azure Spot VMs in AKS: Complete Guide to Cost-Effective Kubernetes Workloads"
pubDate: 2025-05-15
description: "Learn how to leverage Azure Spot VMs in AKS to reduce costs by up to 90% while maintaining production reliability through proper configuration and workload scheduling."
author: "Torstein Skulbru"
isPinned: false
excerpt: "Discover how to harness Azure Spot VMs in your AKS clusters to dramatically reduce compute costs. This comprehensive guide covers everything from understanding spot capacity economics to implementing production-ready configurations with proper failover mechanisms."
image:
  src: "/images/spot-vms.webp"
  alt: "Cloud money clipart"
tags: ["azure", "kubernetes", "aks", "spot-vms", "devops"]
---

Cloud computing costs can quickly spiral out of control, especially when running compute-intensive workloads at scale. For organizations using Azure Kubernetes Service (AKS), Azure Spot Virtual Machines present a compelling opportunity to slash compute expenses by up to 90% compared to standard pay-as-you-go pricing. However, successfully implementing spot instances in production requires understanding their mechanics, limitations, and the proper architectural patterns to ensure reliability.

This comprehensive guide will walk you through everything you need to know about Azure Spot VMs in AKS—from the fundamental economics of spot capacity to hands-on implementation of spot node pools and intelligent workload scheduling strategies.

## Understanding Azure Spot VMs

Azure Spot VMs represent unused compute capacity that Microsoft makes available at significant discounts when their data centers have excess resources. This unused capacity becomes available as "spot" resources at dramatically reduced prices, but with an important trade-off: Azure can reclaim these virtual machines when demand increases or when paying customers need the capacity.

### The Economics of Spot Capacity

The fundamental principle behind spot pricing is based on supply and demand economics in cloud infrastructure. Cloud providers like Azure experience fluctuating demand for their compute resources throughout the day, week, and season. During periods of lower demand, this excess capacity would otherwise sit idle. Instead of letting these resources go unused, Azure offers them at steep discounts to customers willing to accept the possibility of interruption.

**Key Economic Benefits:**

- Cost savings of up to 90% compared to pay-as-you-go pricing
- Access to the same high-performance infrastructure at fraction of the cost
- Ability to run larger workloads within existing budget constraints
- Opportunity to experiment with more resource-intensive applications

**The Trade-off:**
When Azure needs the capacity back for on-demand customers or when the spot price exceeds your maximum bid, your spot instances can be evicted. Azure typically provides a 30-second eviction notice, though this timeframe can vary based on circumstances.

## Spot VM Workload Suitability

Not all applications are good candidates for spot capacity. Understanding which workloads thrive on spot instances versus those that should avoid them is crucial for successful implementation.

### Ideal Candidates for Spot VMs

**Fault-Tolerant Applications:**

- Stateless web servers and API endpoints
- Microservices architectures with proper health checks
- Containerized applications designed for horizontal scaling
- Applications that can gracefully handle node failures

**Batch and Analytics Workloads:**

- Big data processing jobs that can checkpoint progress
- Machine learning training workloads
- CI/CD pipelines and build systems
- Data transformation and ETL processes

**Development and Testing:**

- Development environments
- Automated testing suites
- Staging environments
- Load testing scenarios

### Workloads to Avoid on Spot VMs

**Mission-Critical Systems Without Failover:**

- Single-instance databases without replication
- Legacy monolithic applications
- Systems requiring guaranteed uptime
- Applications with strict latency requirements

**Stateful Workloads Without Proper Backup:**

- Applications that maintain critical state locally
- Systems without external state management
- Workloads that cannot checkpoint progress
- Tightly coupled distributed systems

## Spot Node Pools in AKS

Azure Kubernetes Service provides native support for spot instances through dedicated spot node pools. These node pools are specifically designed to run on spot capacity while integrating seamlessly with AKS's management and scaling capabilities.

### Key Characteristics of Spot Node Pools

**Architectural Constraints:**

- Can only be used as secondary or user node pools
- Cannot serve as system node pools (which host critical Kubernetes components)
- Come with specific Kubernetes taints and labels
- Require corresponding tolerations in pod specifications

**Automatic Labeling and Tainting:**
When you create a spot node pool, AKS automatically applies:

- Label: `kubernetes.azure.com/scalesetpriority:spot`
- Taint: `kubernetes.azure.com/scalesetpriority=spot:NoSchedule`
- Anti-affinity rules for system pods

These mechanisms ensure that only workloads explicitly configured for spot instances will be scheduled on spot nodes.

## Setting Up Spot Node Pools

Let's walk through the process of creating and configuring spot node pools in your AKS cluster.

### Creating a Spot Node Pool

Use the Azure CLI to add a spot node pool to your existing AKS cluster:

```bash
az aks nodepool add \
    --resource-group myResourceGroup \
    --cluster-name myAKSCluster \
    --name spotnodepool \
    --priority Spot \
    --eviction-policy Delete \
    --spot-max-price -1 \
    --enable-cluster-autoscaler \
    --min-count 0 \
    --max-count 10 \
    --node-vm-size Standard_D4s_v3 \
    --no-wait
```

**Key Parameters Explained:**

- `--priority Spot`: Specifies this as a spot node pool
- `--eviction-policy Delete`: Determines what happens when nodes are evicted (Delete or Deallocate)
- `--spot-max-price -1`: Sets maximum price you're willing to pay (-1 means pay up to on-demand price)
- `--enable-cluster-autoscaler`: Enables automatic scaling based on demand
- `--min-count 0`: Allows scaling down to zero nodes when not needed
- `--max-count 10`: Sets maximum number of nodes in the pool

### Understanding Eviction Policies

**Delete Policy (Recommended):**

- Completely removes the VM when evicted
- Faster cleanup and lower costs
- No charges for deallocated VMs
- Suitable for stateless workloads

**Deallocate Policy:**

- Stops the VM but preserves the disk
- Allows for potential restart if capacity becomes available
- Continues to incur storage costs
- Better for workloads that need to preserve local state

### Spot Pricing Strategy

The `--spot-max-price` parameter controls your bidding strategy:

```bash
# Pay up to on-demand price (recommended for production)
--spot-max-price -1

# Set specific maximum price (e.g., $0.50 per hour)
--spot-max-price 0.50

# Use current spot price as maximum
--spot-max-price 0
```

**Recommendation:** Use `-1` for production workloads to minimize eviction risk while still benefiting from spot pricing.

## Scheduling Workloads on Spot Nodes

To run workloads on spot node pools, you must configure your pods with appropriate tolerations and node affinity settings.

### Basic Spot Workload Configuration

Here's a complete example of a deployment configured for spot nodes:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: spot-workload
  labels:
    app: spot-workload
spec:
  replicas: 3
  selector:
    matchLabels:
      app: spot-workload
  template:
    metadata:
      labels:
        app: spot-workload
    spec:
      containers:
      - name: web-server
        image: nginx:latest
        ports:
        - containerPort: 80
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      tolerations:
      - key: "kubernetes.azure.com/scalesetpriority"
        operator: "Equal"
        value: "spot"
        effect: "NoSchedule"
      affinity:
        nodeAffinity:
          preferredDuringSchedulingIgnoredDuringExecution:
          - weight: 100
            preference:
              matchExpressions:
              - key: "kubernetes.azure.com/scalesetpriority"
                operator: In
                values:
                - "spot"
```

### Understanding Tolerations and Affinity

**Tolerations:**
The toleration allows the pod to be scheduled on nodes with the spot taint:

```yaml
tolerations:
- key: "kubernetes.azure.com/scalesetpriority"
  operator: "Equal"
  value: "spot"
  effect: "NoSchedule"
```

**Node Affinity:**
The `preferredDuringSchedulingIgnoredDuringExecution` affinity expresses a preference for spot nodes but allows scheduling on regular nodes if spot capacity isn't available:

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: "kubernetes.azure.com/scalesetpriority"
          operator: In
          values:
          - "spot"
```

### Spot-Only vs. Spot-Preferred Scheduling

**Spot-Only Scheduling:**
Use `requiredDuringSchedulingIgnoredDuringExecution` to ensure pods only run on spot nodes:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
      - matchExpressions:
        - key: "kubernetes.azure.com/scalesetpriority"
          operator: In
          values:
          - "spot"
```

**Spot-Preferred Scheduling (Recommended):**
Use `preferredDuringSchedulingIgnoredDuringExecution` to prefer spot nodes but allow fallback to regular nodes:

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      preference:
        matchExpressions:
        - key: "kubernetes.azure.com/scalesetpriority"
          operator: In
          values:
          - "spot"
```

## Handling Spot Node Evictions

When Azure needs to reclaim spot capacity, it sends an eviction notice to affected nodes. AKS handles this process automatically, but understanding the flow helps you design more resilient applications.

### Eviction Process Flow

1. **Eviction Notice:** Azure sends a notice (typically 30 seconds before eviction)
2. **Node Cordoning:** AKS marks the node as unschedulable
3. **Pod Draining:** Kubernetes gracefully terminates pods on the node
4. **Rescheduling:** Pods are rescheduled on available nodes
5. **Node Cleanup:** The evicted node is removed from the cluster

### Configuring Graceful Shutdowns

Ensure your applications handle termination signals properly:

```yaml
spec:
  containers:
  - name: app
    image: myapp:latest
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 15"]
  terminationGracePeriodSeconds: 30
```

## Best Practices for Production Use

### 1. Implement Hybrid Node Pool Strategy

Don't rely solely on spot capacity. Maintain a mix of spot and on-demand node pools:

```bash
# Create on-demand node pool for critical workloads
az aks nodepool add \
    --resource-group myResourceGroup \
    --cluster-name myAKSCluster \
    --name ondemandpool \
    --priority Regular \
    --enable-cluster-autoscaler \
    --min-count 1 \
    --max-count 5

# Create spot node pool for cost-optimized workloads
az aks nodepool add \
    --resource-group myResourceGroup \
    --cluster-name myAKSCluster \
    --name spotpool \
    --priority Spot \
    --enable-cluster-autoscaler \
    --min-count 0 \
    --max-count 10
```

### 2. Use Pod Disruption Budgets

Protect critical workloads during evictions:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: spot-workload-pdb
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: spot-workload
```

### 3. Implement Health Checks

Ensure rapid detection of unhealthy pods:

```yaml
spec:
  containers:
  - name: app
    livenessProbe:
      httpGet:
        path: /health
        port: 8080
      initialDelaySeconds: 30
      periodSeconds: 10
    readinessProbe:
      httpGet:
        path: /ready
        port: 8080
      initialDelaySeconds: 5
      periodSeconds: 5
```

### 4. Design for Horizontal Scaling

Ensure your applications can scale horizontally:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: spot-workload-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: spot-workload
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

## Testing Spot Evictions

Azure provides tools to test spot eviction scenarios:

```bash
# Simulate eviction for testing
az vm simulate-eviction \
    --resource-group MC_myResourceGroup_myAKSCluster_eastus \
    --name aks-spotpool-12345678-vmss000000
```

This command helps you validate that your applications handle evictions gracefully in a controlled manner.

## Cost Optimization Strategies

### 1. Right-Size Your Spot Instances

Choose VM sizes that match your workload requirements:

```bash
# For CPU-intensive workloads
--node-vm-size Standard_F4s_v2

# For memory-intensive workloads  
--node-vm-size Standard_E4s_v3

# For general-purpose workloads
--node-vm-size Standard_D4s_v3
```

### 2. Leverage Multiple VM Families

Diversify across different VM families to reduce eviction risk:

```bash
# Create multiple spot pools with different VM types
az aks nodepool add --name spot-compute --node-vm-size Standard_F4s_v2
az aks nodepool add --name spot-memory --node-vm-size Standard_E4s_v3
az aks nodepool add --name spot-general --node-vm-size Standard_D4s_v3
```

### 3. Use Cluster Autoscaler Effectively

Configure the cluster autoscaler to optimize for cost:

```bash
az aks update \
    --resource-group myResourceGroup \
    --name myAKSCluster \
    --cluster-autoscaler-profile \
        scale-down-delay-after-add=10m \
        scale-down-unneeded-time=10m \
        skip-nodes-with-local-storage=false \
        skip-nodes-with-system-pods=false
```

## Additional Cost Optimization Strategies

While spot VMs offer the most dramatic cost savings, they work best as part of a broader cost optimization strategy. Here are a few other techniques worth considering:

### Quick Cost-Saving Tips

**Reserved Instances:** For predictable, long-running workloads, Azure Reserved Instances can provide up to 72% savings with a 1-3 year commitment. These work well for your stable, on-demand node pools that complement spot capacity.

**Scheduled Shutdowns:** Development and test environments can achieve 73% cost reduction by running only during business hours (e.g., weekdays 8 AM - 6 PM, weekends off).

**Right-Sized Node Pools:** Instead of using one VM type for everything, create specialized node pools:

- CPU-optimized (Standard_F series) for compute workloads  
- Memory-optimized (Standard_E series) for data processing
- General-purpose (Standard_D series) for balanced workloads

This approach can result in 30-40% additional savings through better resource utilization.

**Watch Hidden Costs:** Set daily limits on Log Analytics ingestion and consider open-source alternatives to Azure Defender ($2/core/month) like Falco for security monitoring.

These strategies, combined with spot VMs, can reduce your total AKS costs by 70-90% while maintaining reliability. For more detailed cost optimization techniques, check out resources like [Zartis's AKS cost optimization guide](https://www.zartis.com/minimizing-costs-aks/).

## Conclusion

Azure Spot VMs in AKS offer a powerful way to dramatically reduce compute costs while maintaining production reliability when implemented correctly. The key to success lies in understanding the trade-offs, designing applications for resilience, and implementing proper monitoring and alerting.

By following the patterns and practices outlined in this guide, you can:

- Achieve cost savings of up to 90% on compute resources
- Maintain high availability through intelligent workload scheduling
- Build resilient applications that gracefully handle node evictions
- Implement effective monitoring and alerting for spot workloads

Remember that spot instances are not a silver bullet—they require thoughtful architecture and operational practices. Start with non-critical workloads, gain experience with the eviction patterns, and gradually expand to more critical applications as your confidence and expertise grow.

The combination of proper configuration, monitoring, and application design will enable you to harness the full potential of Azure Spot VMs while maintaining the reliability your production workloads demand.

---

*For more advanced patterns including automatic failback to spot instances and priority-based cluster autoscaling, check out our follow-up guide on [Slash Your AKS Costs: Run Resilient Production Workloads on Azure Spot VMs](/posts/slash-aks-costs-production-workload-spot-vms)*
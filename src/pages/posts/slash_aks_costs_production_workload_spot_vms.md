---
layout: ../../layouts/post.astro
title: "Slash Your AKS Costs: Run Resilient Production Workloads on Azure Spot VMs"
pubDate: 2025-06-06
description: "Learn how to implement intelligent failover and failback mechanisms for Azure Spot VMs in production AKS environments, achieving up to 90% cost savings while maintaining high availability through automated orchestration between spot and on-demand resources."
author: "Torstein Skulbru"
isPinned: true
excerpt: "Azure Spot VMs offer up to 90% cost savings, but production adoption brings complex challenges beyond basic setup. This guide tackles the real problems teams face: automatic failover during spot evictions, intelligent failback when capacity returns, and seamless orchestration between spot and on-demand resources. We'll explore how to combine AKS features, Kubernetes best practices, and tools like the descheduler to build a resilient system that maximizes cost savings without sacrificing reliability."
image:
  src: "../images/slash-aks-containers.jpg"
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

## Advanced Spot VM Strategies for Production

[Continue with the advanced content about priority expanders, descheduler, failback mechanisms, etc.]

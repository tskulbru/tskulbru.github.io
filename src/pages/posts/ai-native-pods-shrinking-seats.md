---
layout: ../../layouts/post.astro
title: 'AI-Native Pods and the Shrinking Number of Seats'
pubDate: 2026-05-08
description: 'This week''s tech layoffs aren''t just about cost-cutting. They''re a structural reorganization toward AI-native pods — the working shape solo builders have lived in for years. The seats disappearing belong to people who can''t operate the system.'
author: 'Torstein Skulbru'
isPinned: true
excerpt: 'Coinbase, Microsoft, Oracle. Same week, same explanation. The headline is layoffs. The actual story is the team being rebuilt around the agent.'
image:
  src: '/images/ai-pods-hero.webp'
  alt: 'A traditional org chart on the left dissolving into a single person directing AI agents on the right'
tags: ['ai', 'industry', 'tech-layoffs', 'careers', 'llm', 'commentary']
---

Earlier this week, Coinbase laid off 14% of its workforce — roughly 660 people. The CEO's stated reason wasn't market conditions or restructuring debt or any of the usual euphemisms. It was that AI now lets engineers ship in days what used to take a team weeks, and that non-technical employees are increasingly writing code themselves. The day after, Brian Armstrong told a podcast that mass layoffs are coming to "every company."

He isn't predicting. He's describing a wave that's already arrived. Microsoft and Meta announced roughly 20,000 cuts combined in April, with AI and Copilot teams explicitly carved out of any freeze. Oracle workers reported being terminated after training the AI that replaced them. The first quarter of 2026 saw nearly 80,000 tech layoffs industry-wide. Of those, roughly half were attributed directly to AI.

The headlines are about layoffs. The actual story is more interesting.

## The shape, not the headcount

Coinbase isn't just cutting 14%. It's inverting its org chart. Pure managers are being replaced by what the company is calling "player-coaches": leaders who supervise people but also ship as individual contributors themselves. Below them, the company is piloting "AI-native pods" — small teams, sometimes a single person, who direct AI agents that cover what used to require a separate engineer, designer, and product manager.

That last detail is the part worth sitting with. The basic unit of *what one person can do* has gotten dramatically larger. The cuts are downstream of that. If a one-person pod can ship what a five-person team used to ship, the four people are not strictly necessary. The org chart is the dependent variable.

Microsoft is taking the same approach with different optics. Voluntary buyouts aimed at long-tenured employees, AI and Copilot teams exempt, headcount drifting down without the PR damage of a single mass-layoff announcement. Same direction, slower drift.

![A pyramid-shaped org chart inverting itself, with managers being reshuffled into player-coach roles that combine leadership with shipping](/images/org-chart-inversion.webp)

## I've been working in a pod for years

The thing nobody is saying clearly is that this shape has existed for a while — just on the other side of the company-versus-solo line.

Most of what I've shipped over the last two years was built by exactly one person. [MyVisualRoutine](https://myvisualroutine.com), the most successful of the bunch, is an iOS and Android app for families using visual schedules and choice boards to help kids follow daily routines. [Plask](/posts/building-plask-ga4-analytics-saas) is a multi-tenant SaaS that connects to Google Analytics, runs statistical anomaly detection, and writes weekly digests with an LLM. [Mockingjay](/posts/building-mockingjay-secure-video-recorder) is an iOS app for encrypted video recording with real-time cloud backup. [Stao](/posts/building-stao-standing-desk-companion) is a cross-platform reminder app on five operating systems. [Issueflow](/posts/how-i-built-issueflow-turn-slack-conversations-into-github-issues-with-ai) turns Slack threads into structured GitHub issues. Across all of them I did the engineering, the design, the copy, the App Store screenshots, the OAuth verification, the billing, the support emails, and most of the marketing.

That isn't a brag — it's the only reason any of them shipped. There was no team. There was me, an LLM I trust to write boilerplate, another LLM I argue with about architecture, and a small set of tools that didn't exist in this form three years ago.

Coinbase is rebuilding itself around that shape. So is Microsoft, so is Meta, more quietly. The companies cutting people right now aren't moving to a new structure. They're moving to one that solo builders have already been living in for a while.

## The seat that's disappearing

This is where the story turns less optimistic.

The seat being eliminated isn't junior engineer. Every recent piece predicting the death of entry-level engineering has been overconfident. Junior engineers using AI well are dramatically more productive than they were two years ago, and the companies that figure out how to onboard them into AI-native workflows will have a significant advantage.

The seats that are actually disappearing belong to people who sit next to engineers but can't operate the system themselves. Pure managers. Project coordinators. Quality assurance roles where the AI now matches median performance. Customer support agents whose work falls within the competence of a well-tuned LLM. Klarna replaced roughly 700 customer service agents with an AI assistant that now handles about 70% of their interactions. Coinbase is collapsing layers of management into player-coach roles that require shipping on top of leading.

In every case the underlying logic is the same: if your contribution to a software company is something an AI can do, and you can't direct that AI to do more than your replacement could, your role is moving down a list of priorities that the budget will eventually catch up to.

The window to learn this is closing on a much shorter timeline than people are pricing in. "I'll get around to the AI tools later" was a defensible position in 2024. In 2026 it's a stated preference for a smaller set of opportunities.

![Empty chairs being quietly removed from a conference room while a single person at the head of the table works alongside several glowing agents](/images/shrinking-seats.webp)

## The other side of the same shift

Here's the part the layoff coverage almost always misses.

The same change that's taking those seats out of large companies is what made it possible for a single person to ship what I shipped this year. The leverage is real, and it's distributed asymmetrically. It's hardest to capture inside a company with 5,000 people, an org chart, and a quarterly planning cycle. It's easiest to capture as a single operator who can rewrite their own working shape every Monday morning.

If you read the news only as "AI takes jobs," you miss the more accurate version: AI made the minimum viable team smaller. That has consequences for incumbents — they have to dismantle structures they spent a decade building. It also has consequences for solo builders and small operators, who now have access to leverage that was previously locked behind hiring a team.

The displacement and the leverage are the same event seen from two angles. People are losing their jobs and other people are shipping ambitious things alone. Both are happening at scale, often inside the same week.

## What actually matters now

A few things I think are true, briefly.

The job is no longer "write the code." It's deciding what should be built and orchestrating the system that builds it. Engineers who treat their role as typing characters into a file are competing with the part of the work that has been most thoroughly automated.

Prompting is the floor, not the ceiling. Treat it like learning git in 2012 — basic professional literacy that you no longer get to opt out of. The interesting skills are upstream: judgment about what to build, taste about what's good, the ability to recognize when an agent is wrong before you ship its mistake.

If you're non-technical inside a software company, the move probably isn't to learn to code. It's to learn to direct the system — which is a different and more durable skill. The seat for "person who knows the domain and can drive AI agents through a problem" is expanding. The seat for "person who routes information between technical people" is not.

Solo-builder economics quietly got really good. If you've been on the fence about shipping something alone, the math is more in your favor than it has ever been.

## The honest version

This is both genuinely exciting and genuinely brutal, and it's often the same person on both sides of the line.

The Oracle workers who trained the AI that replaced them are not a metaphor. The Coinbase managers being recategorized into player-coach roles are real people with mortgages. The AI-native pod that lets one person ship a SaaS is also real, and it's going to put a lot of people out of work over the next two years.

I don't know how to resolve that tension, and I'm suspicious of anyone who claims to. The shape of work is changing faster than we can write clean takes about it. The most honest thing I can say is that the companies announcing layoffs this week are catching up to a structure that's already been operating, just outside their walls. The people shipping ambitious things alone right now are catching up to a leverage curve that's still bending upward.

It's scary. It's interesting. It's both at once. Pick a position carefully.

---

_If you're trying to figure out where to start in practice, I teach a [4-week live course on agentic coding](/courses/agentic-coding) — for developers, PMs, founders, and non-technical folks who need to ramp on directing AI agents in real work. Cohort 2 dates aren't set yet; DM me on [LinkedIn](https://www.linkedin.com/in/tskulbru) or [Bluesky](https://bsky.app/profile/tskulbru.dev) if you want first notice._

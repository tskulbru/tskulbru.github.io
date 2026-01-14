---
layout: ../../layouts/post.astro
title: "I Built IssueFlow: Turn Slack Conversations into GitHub Issues with AI"
pubDate: 2025-10-23 # Update with your publish date
description: "How I lost dozens of minutes a week to copy-pasting Slack conversations into GitHub, and built an AI tool to solve it."
author: "Torstein Skulbru"
isPinned: false
excerpt: "How I lost dozens of minutes a week to copy-pasting Slack conversations into GitHub, and built an AI tool to solve it."
image:
  src: "/images/totally-serious-working-pic.png"
  alt: "Cloud money clipart"
tags: ["side-project", "ai", "slack", "github", "developer-tools"]
modifiedDate: 2026-01-14
blueskyUri: "at://did:plc:rmnykyqh3zleost7ii4qe5nc/app.bsky.feed.post/3m3tszzv3o22n"
---

Three weeks ago, I lost a critical bug report in Slack.

It wasn't dramatic. No production outage. No angry users. Just a thoughtful conversation in our #engineering channel about a edge case that was causing incorrect data in certain scenarios. Seven messages. Good context. Clear reproduction steps. Someone even suggested a fix.

Two days later in sprint planning: "Hey, what happened to that bug we talked about?"

Blank stares. Someone scrolled back through 200 messages. Found it. Then spent 15 minutes copying pieces into a GitHub issue, trying to remember who said what and what the actual problem was.

The context was gone. The energy was gone. We'd already spent mental cycles on this problem—twice.

That's when I realized: **this happens every single day.**

## The Problem Nobody Talks About

We've gotten really good at building developer tools for the "real work." Code editors are amazing. CI/CD pipelines are fast. Deployment is one command.

But the meta-work? The boring stuff between conversations and action? Still manual. Still tedious. Still eating hours every week.

Here's what I observed on my team:

- **~30% of Slack conversations** about bugs or features never become GitHub issues
- **15 minutes per day** spent context-switching between Slack and GitHub
- **Critical details lost** because someone paraphrased instead of copying the full conversation
- **Duplicate issues** because nobody remembered we already discussed this in a thread last week

This isn't a tools problem. Slack is great for conversations. GitHub is great for tracking work. The problem is the gap between them.

The problem is the **manual copy-paste tax** we all pay.

## Why Existing Solutions Don't Work

I tried the obvious things first:

**Zapier/Make:** Too rigid. Can't handle the nuance of "is this conversation actually actionable?" and "what parts matter?" You'd just end up with 100 GitHub issues that say "lol yeah" or "coffee emoji."

**Slack reminders:** Still manual. You have to remember to create the issue yourself later. The context is still lost.

**GitHub Slack integration:** Shows you GitHub updates in Slack. Doesn't help with the Slack → GitHub direction.

**Manual discipline:** "Everyone should just create issues immediately!" In theory, yes. In practice, no. Conversations are exploratory. You don't know it's an issue until message 7 of 12.

What I needed was something that:
1. Understood conversation context (not just keywords)
2. Extracted what actually mattered (not everything)
3. Structured it properly for GitHub
4. **Got out of the way**

So I built it.

![](/images/issueflow-screenshot.png)

## Introducing IssueFlow

IssueFlow is an AI-powered bot that lives in your Slack workspace and watches for conversations that should become GitHub issues.

Here's how it works:

### The Simple Flow

1. Your team is discussing something in Slack (bug, feature idea, customer feedback)
2. Someone mentions `@issueflow` when they realize "this should be tracked"
3. IssueFlow reads the conversation context (last 20 messages)
4. AI generates a structured GitHub issue with:
   - Clear title
   - Summary of the problem/request
   - Relevant context from the conversation
   - Key participants
5. You review and approve (or edit)
6. IssueFlow creates the GitHub issue
7. Done. Back to work.

**Total time: 15 seconds.**

No copy-pasting. No lost context. No "wait, what were we talking about again?"


### The Technical Challenge

The hardest part wasn't the Slack or GitHub APIs. Those are well-documented and straightforward.

The hard part was **context extraction**.

When someone mentions `@issueflow` in message 15 of a thread, which messages actually matter for the issue?

- Too much context and the AI gets confused by tangents and jokes
- Too little context and you lose the critical detail that explains the problem

Here's what I learned:

#### Naive Approach (Doesn't Work)
```
Take last 10 messages → send to GPT-4 → generate issue
```

**Problem:** Conversations drift. Message 8 might be about lunch plans. Messages 1-3 might be from a different topic entirely.

#### The Solution: Semantic Search + Rolling Window

1. **Semantic Search**: Use embeddings to find messages semantically similar to the @issueflow mention
2. **Rolling Window**: Track conversation flow—if messages are within 2 minutes of each other, they're probably related
3. **Structured Prompting**: Give the AI explicit instructions:
   - "Extract the problem statement"
   - "Identify who's affected"
   - "Find any proposed solutions"
   - "Ignore jokes, off-topic tangents, and meta-discussion"

The results are surprisingly good. The AI understands that:
- "This breaks on Safari" is relevant
- "lol same" is not relevant
- "Here's a workaround: [code]" is very relevant
- "Anyone want coffee?" is not relevant

### The Architecture

For the curious technical folks:

**Stack:**
- Next.js 14 (App Router) for the API and web app
- Supabase (PostgreSQL) for data + auth
- OpenAI GPT-4 for conversation analysis
- Slack Bolt SDK for Slack integration
- Octokit for GitHub API

**Key Design Decisions:**

1. **Serverless-first**: Deployed on Vercel. Event-driven. No always-on servers.
2. **Async processing**: Slack webhooks respond in <3 seconds. AI processing happens in background.
3. **User approval required**: No automatic issue creation. Human reviews AI output first.
4. **Encryption**: OAuth tokens stored with AES-256-GCM encryption.

It's a fairly standard Next.js app with careful attention to webhook timing (Slack expects responses in <3 seconds) and rate limiting (per-organization quotas).

## What I Learned Building This

### 1. The Context Window Problem is Everywhere

Once you start thinking about "extract meaningful context from conversation," you realize this problem is **everywhere**:

- Meeting notes → Action items
- Support tickets → Bug reports
- Customer feedback → Feature requests
- Standup updates → Sprint planning

IssueFlow is just the first use case. The pattern is universal.

### 2. AI Doesn't Need to Be Perfect

My initial instinct was to over-engineer the context extraction. "What if it misses something important?"

But here's the thing: **humans miss stuff too.**

When you manually create an issue from a Slack thread, you're skimming, paraphrasing, and forgetting details. The AI is at least consistent and catches things you'd miss.

And because there's a human review step, the AI just needs to be "good enough" (which GPT-4 absolutely is).

### 3. The Best Tools Disappear

The initial version had too many options. "Do you want to include attachments? Which repository? Add labels? Assign to someone?"

I stripped it all away. Now it's just:
- Mention `@issueflow`
- Review
- Approve

That's it. The tool gets out of your way. You barely think about it.

### 4. Building for Yourself is Powerful

I'm solving my own problem. Every design decision came from real pain I experienced:

- Why 20 messages of context? Because that's how long our typical threads are.
- Why Slack + GitHub specifically? Because that's what we use.
- Why AI instead of rules? Because conversations are too nuanced for rules.

When you're your own user, you know exactly what matters.

## Try IssueFlow (It has a 3-Day Free Trial)

The MVP is live and ready to be played around with.

**Perfect for:**
- Small to medium engineering teams (5-50 people)
- Teams already using Slack + GitHub
- Anyone tired of the copy-paste tax

**What you get:**
- AI-powered conversation → issue creation
- Unlimited Slack workspaces
- Unlimited GitHub repositories

**What it's NOT (yet):**
- Not for massive enterprises (no SSO, no advanced admin controls)
- Not for non-GitHub issue tracking (Jira, Linear, etc.)
- Not automatic (still requires human review)

I'm actively looking for early users to test it and tell me what breaks.

**Try it here: [https://issueflow.io](https://issueflow.io)**

Sign up takes 2 minutes. You'll connect your Slack workspace and GitHub account, and you're ready to go.

## What's Next

I'm treating this as a real product, not just a side project. Here's what I'm working on:

**Short-term (next 4 weeks):**
- Better error messages when things go wrong
- Conversation threading (so follow-up Slack messages update the GitHub issue)
- More detailed usage analytics dashboard

**Medium-term (next 3 months):**
- Support for Linear, Jira (if there's demand)
- Custom prompts (customize how AI structures issues for your workflow)
- Slack → Notion, Slack → Asana (same pattern, different targets)

**Longer-term vision:**
Eliminate all meta-work. If it's a conversation that should be structured data somewhere, it should happen automatically (with human oversight).

## The Honest Part

This is an early MVP. There will be bugs. The AI will occasionally miss context or summarize something weirdly. The UI is functional but not beautiful.

I'm not trying to sell you enterprise software. I'm sharing something I built for myself that you might find useful.

If you try it and it doesn't work for you, that's totally fine. If you try it and have ideas to make it better, **please tell me.** DM me on Bluesky (@tskulbru.dev), or send a support ticket here [https://issueflow.io/contact/support](https://issueflow.io/contact/support).

I'm building this in public. Early users shape what gets built next.

## Final Thought

We spend so much time optimizing our code, our deployments, our CI/CD pipelines. All good things.

But we barely think about optimizing the invisible work—the copy-pasting, the context-switching, the "wait, where was that conversation again?"

That's 5-10 hours per week per engineer. Across a team of 10, that's **500 hours per year** spent on meta-work instead of building.

IssueFlow is my attempt to get some of that time back.

If you're losing hours to the Slack-GitHub gap, give it a shot: **[https://issueflow.io](https://issueflow.io)**

And if you're building tools to eliminate meta-work in other areas, I'd love to hear about it. This problem space is wide open.

*IssueFlow is one of my side projects. Check out my [portfolio](/portfolio) to see what else I'm building.*

---

*If this resonates with you, share it with your engineering team. Someone on your team is losing time to this problem right now.*

---

## Appendix: FAQ


**Q: How much does it cost?**\
A: See the pricing table on the website, [https://issueflow.io/#pricing](https://issueflow.io/#pricing)

**Q: Do you see our Slack messages?**\
A: IssueFlow only reads messages in channels where the bot is invited AND only when explicitly mentioned. We don't scan your entire workspace.

**Q: What about privacy/security?**\
A: All OAuth tokens are encrypted at rest. We use Supabase Row Level Security. OpenAI doesn't train on your data (we use the API, not the web interface).

**Q: Can I self-host it?**\
A: Not yet, but if there's demand I'll open-source parts of it or offer a self-hosted option.

**Q: Does it work with GitHub Enterprise?**\
A: Not yet, but planned for sometime in 2026 depending on demand.

**Q: What if the AI gets it wrong?**\
A: You review everything before it's created. If the AI misses something, edit it. If it's consistently wrong, let me know so I can improve the prompts.

**Q: Can I customize how issues are structured?**\
A: Not yet, but "custom prompts" is on the roadmap.

**Q: Why did you build this instead of using Github Slack Integration?**\
A: I tried them all. They either don't handle the nuance of conversation context or require too much manual configuration. I wanted something that "just works."

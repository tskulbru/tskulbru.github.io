---
layout: ../../layouts/post.astro
title: 'I Lost Track of What My Agents Were Doing, So I Gave Them a Shared Notebook'
pubDate: 2026-09-11
description: 'Running parallel Claude Code sessions across a dozen repos, I kept losing the thread of long efforts that branched into many PRs and months of blockers. GitHub was the wrong place for in-flight state, a knowledge base like gbrain answered the wrong question, and a dashboard would only have fixed one of three problems. What I needed was something in between. This is how I landed on Beads, added mardi-gras on top, and why Gas Town is on the horizon but not on the roadmap.'
author: 'Torstein Skulbru'
isPinned: true
excerpt: "My agents weren't the bottleneck. I was, holding the dependency graph of six months of branching work in my head. The fix wasn't a better wiki or more GitHub comments. It was a private work graph that sits between the two."
image:
  src: '/images/beads-local-shadow-hero.webp'
  alt: 'A dense pile of brightly coloured beads in red, pink, yellow, blue, green and white, seen from above'
tags: ['claude-code', 'ai', 'agents', 'beads', 'developer-tools', 'productivity', 'workflow']
blueskyUri: 'at://did:plc:rmnykyqh3zleost7ii4qe5nc/app.bsky.feed.post/3mvbck2lxnc2l'
---

I live in tmux. On a normal day I have four tmux sessions open, roughly one per area of work, and each of them holds somewhere between twenty and thirty windows with a Claude Code chat in it. That's close to a hundred conversations, spread over a platform of 30-plus Go services, a mobile app, infrastructure repos and a data pipeline. At any moment a handful are actively working: one implementing, one reviewing PRs, one babysitting a deploy, one halfway through an investigation I'll get back to after lunch. The rest are parked, each holding context I don't want to lose. The agents are fine with this. The part that broke was me.

Here's what I wrote to Claude one afternoon, typos and all:

> I struggle keeping track of all the work you and your fellow instances are doing. We work across so many repos, and so many paralelle tasks at once... often we start on a large task which branches out into multiple prs and sub issues, but i/we loose track of it all... Someone surely must have built something, because the cognitive drain for me is huge when working like this.

The number of chats isn't really the problem, though. It's how they come about. I rarely get to start something and finish it in one go. Day-to-day operations pull me sideways: an alert fires, a colleague needs a hand, a deploy misbehaves. Ideas pop into my head halfway through something else and get their own chat so I don't lose them. And some implementations turn out to be a hornet's nest. You start on one issue, find three things it depends on, each of those turns up something broken, and before lunch one task has spun off into ten or fifteen parallel chats. Each one makes sense on its own. Together, nobody holds the whole picture, and that includes me.

![One terminal session branching out into a sprawling tree of parallel chats, with alerts and ideas pulling threads sideways while a lone person watches](/images/hornets-nest-parallel-chats.webp)

The concrete case was an archiving effort for our vehicle tracking data that had been running for months. It's the kind of work where there's always something that blocks something else that needs fixing first. Plan it, implement it, babysit it into deployment, discover the next blocker, repeat. The individual steps were never hard. Knowing where we were was.

This also capped how autonomous the agents could be. Claude can already pick up a GitHub issue, implement it, run the gates and open a PR. It works well for self-contained issues. But the issue only tells half the story. It doesn't know that another chat is halfway through a change to the same service, that the migration it depends on is sitting in dev waiting for a soak, or that I decided last Tuesday to hold off until a customer confirms something. None of that lived in GitHub. It lived in other chats and in my head. So an agent working from GitHub alone would happily do the right thing in the wrong order, and I had to stay in the loop as the only one who knew about the cross-cutting, in-flight state.

## The problem, stated properly

When I pulled it apart, "losing track" was actually three different problems wearing one coat:

1. **What is blocked on what, and what's ready now?** A dependency graph that lived only in my head.
2. **Which session did what?** Chat IDs, summaries, the reasoning behind a decision. At one point I found a PR that had been stuck for weeks and wrote: "i cant remember why we thought that, and its kinda stuck right now until we decide." The reasoning had only ever lived in a chat that was long gone.
3. **What do we know?** Facts about the systems, gotchas, past incidents. This one was mostly solved already.

Any tool I picked had to be judged against all three.

## Why not just GitHub

Claude's first answer was the sensible, boring one: don't build a framework. GitHub already has sub-issues, progress fields and linked PRs. A small status view on top would cover "how far along are we." Its diagnosis was "a reporting gap, not an orchestration gap."

I pushed back, because GitHub is the wrong place for most of this:

> one thing is the issues in github, but often i want info that isnt or shouldnt necessarily be tracked there. Like chat ids, summaries etc. ... Im not sure all the in-flight/development information should be put on github. I think maybe i want something which utilizes github issues and projects, but has some sort of local shadow for in-flight things

GitHub issues are a public contract. Colleagues read them. Product reads them. A six-month issue that gets a new bot comment every time an agent session touches it turns into a wall of noise nobody reads, including me. Session URLs, "blocked until I decide X," "the deploy is sitting in dev waiting for a soak": that's scratch state. It's valuable to me and my agents, and it's clutter for everyone else.

So GitHub stays the source of truth for *what* we're doing. It just can't be the place where *how it's going* lives.

## Why not gbrain, or a memory vault

The other direction was knowledge tools. I asked how this related to things like Garry Tan's gbrain or Karpathy's LLM wiki idea. The answer reframed the whole thing for me:

> They solve a different layer. Both gbrain and Karpathy's LLM wiki are knowledge stores. Beads is a work graph.

I already had a knowledge store. Claude Code's auto-memory directory had grown to a couple of hundred small files about our systems, basically a small Karpathy-style wiki. It answers question 3 well. But no amount of better wiki fixes question 1, because a wiki page has no notion of *ready* versus *blocked*. My vehicle tracking effort was documented across six separate memory files. Everything was written down. There was just no spine connecting it.

gbrain specifically also brings Postgres, embeddings and cron enrichment, which is a lot of machinery for a few hundred files. It's designed around one resident agent, not many short-lived Claude Code sessions that come and go all day.

## Why not a dashboard

The obvious engineer's move was to build a dashboard: pull issues, PRs and deploy status into one page, and look at it every morning. It could have worked. I just don't think it would have lasted.

For one, it would be brittle. A custom dashboard is one more piece of software to maintain, with its own data model, its own integrations and its own ways of breaking. The first time an API changes or I restructure how efforts are tracked, it goes stale, and a stale status page is worse than none because you trust it.

It's also more UI than I need. I don't want charts and swimlanes. I want to know what's blocked, what's ready and where I left off, and a list in a terminal answers that fine.

The biggest problem is who keeps it current. If the dashboard owns its own state, every one of those hundred chats has to know about it and remember to update it, in the right format, at the right moment. That's a lot of ceremony to push into every session, and agents are exactly as reliable at optional bookkeeping as people are. If it only reads from GitHub instead, it can't show the things I deliberately keep off GitHub: the blocker that isn't an issue, the chat that made a decision. And it does nothing for the agents themselves. A new session starting cold still has no idea what the last one left half-done.

What I needed was the data layer, not the UI: something agents write to naturally as part of their work, with any view on top being optional and cheap.

## Something in between: Beads

What fit was [Beads](https://github.com/steveyegge/beads) (`bd`), Steve Yegge's issue tracker built for coding agents. It's a local database of work items with dependencies, `bd ready` and `bd blocked` queries, external references to GitHub issues and PRs, and free-form notes. It's the "local shadow" I'd asked for, almost word for word.

If you want the reasoning from the source, read Steve's [introduction to Beads](https://steve-yegge.medium.com/introducing-beads-a-coding-agent-memory-system-637d7d92514a). A lot of what frustrated me about keeping agents on track across long, messy work is in there, put better than I managed in my typo-riddled message to Claude.

Claude also floated an even lazier option: one markdown file per effort. It rejected that itself, and I agreed. You'd rebuild dependency resolution by hand within a month.

That gave me three layers, each with one job:

| Question | Layer |
|---|---|
| What are we doing? (public) | GitHub issues and projects |
| What's blocked, what's ready, which session did what? (private, in-flight) | Beads |
| What do we know? | Memory / wiki |

Or in Claude's words: GitHub issues are for the world. Beads is your private notebook of what is blocked on what.

![A dependency graph of work items sitting between a GitHub issue board and a stack of terminal sessions](/images/beads-between-github-and-terminals.webp)

### How it's wired

A few decisions made this work in practice:

- **One shared database:** I start every session from an umbrella directory that isn't itself a git repo, so the per-repo discovery Beads does by default didn't fit. One `BEADS_DIR` environment variable in the Claude Code settings points every session, subagent and worktree at the same database. Local only, no sync.
- **Efforts and tasks:** long-running efforts are top-level beads. Tasks hang under them with a `repo:<name>` label and an external ref to the GitHub issue or PR. A few extra labels (`human-gate`, `needs-verification`, `destructive`, `deadline`) mark the things I actually need to act on.
- **The database is the one in charge:** I'd wanted an "agent in charge" per repo. Claude pointed out that can't exist in Claude Code, because every agent dies with its session. What survives is the database. So every agent run is bookended instead: at the start it finds the bead, checks `bd blocked` and claims it with `bd update --claim`; at the end it writes what happened into the bead's notes and closes it or marks it blocked.
- **GitHub gets one comment:** each issue gets a single status comment with a hidden marker, edited in place. Stakeholders get a current summary without a comment per session.
- **A handful of verbs:** after the first hour I admitted "i dont quite understand how to use all of this." Day to day it comes down to a few `bd` commands: `bd ready` for what can move now, `bd blocked` for what can't and why, `bd show <id>` to load a bead's history into a fresh session, and `bd note` and `bd close` to leave the trail behind.

Seeding ten efforts, about 130 beads so far, was done by parallel subagents reading memory and live GitHub. Even that was useful: it surfaced a PR that had been in conflict for a month and a rollout that was a month further along than I remembered.

### Gotchas

- `bd init` injects a block into your `CLAUDE.md` telling agents to use Beads instead of other memory, and writes an `AGENTS.md` copy. With an existing memory setup I didn't want either, and removed both.
- `bd show --json` hides closed dependencies, so blocker checks use `bd blocked` instead.
- Children inherit parent labels by default. Making an effort depend on its last child creates a cycle.
- Claims are keyed to the user, not the session, so two parallel sessions can both claim the same bead. Fine at my scale, and something to guard against later.

### What about a team?

The biggest open question is that my setup is local. It's one database on one laptop, and that's fine while it's my private notebook. But I work in a team, and plenty of efforts cross over to other people. If a colleague picks up the next step in the archiving effort, my beads, the blockers and the chats that made decisions, are sitting on my machine where they can't see them.

My first assumption was that Beads simply can't share, short of pointing everyone at the same SQLite file somehow. That turns out to be out of date. Current Beads stores everything in [Dolt](https://github.com/dolthub/dolt), a SQL database with Git-style version control built in, and sharing is part of the design:

- **Remotes:** `bd dolt remote add`, then `bd dolt push` and `bd dolt pull`, with Git-like merges of the issue data. A shared remote on DoltHub, a self-hosted server or cloud storage turns a personal database into a team one.
- **A shared server:** Beads already talks to a `dolt sql-server` under the hood. Point everyone's `host` setting at one shared server and you have one live database instead of copies to sync.
- **Federation:** `bd federation` syncs separate workspaces as peers, each keeping its own database but exchanging updates.

I haven't tried any of these. I kept it local on purpose while testing, so I can't say how well merges behave when two people edit the same effort. The harder question is what to share. My notes were written for me: half-formed doubts, "blocked until I decide," links to chats. Sharing the database means deciding which parts of the in-between layer belong to the team and which stay in my own notebook. That's the next experiment.

## Adding mardi-gras

The CLI is fine for agents. For me, scanning 130 beads in a terminal list isn't. So I added [mardi-gras](https://github.com/quietpublish/mardi-gras) (`mg`), a single-binary TUI for Beads. It shows a "parade" of in-progress, ready, blocked and done work, and can also sit in the tmux status line. This is where the dashboard itch got scratched after all, but as a view over the shared notebook rather than a separate system.

![The mardi-gras TUI showing a parade of in-progress, ready, blocked and done beads](/images/mardi-gras-demo.gif)
*Demo from the [mardi-gras repo](https://github.com/quietpublish/mardi-gras).*

I use it as a read-only view. I browse the parade, find the bead, and hand its ID to a Claude session, so the work still goes through our normal flow with worktrees, bead bookkeeping and our PR conventions. That split works well: humans look, agents write.

mg can do more than look, though. It can "sling" a bead straight to an agent, and its target list includes things like a *mayor* or a *polecat pool*. Those names come from Steve Yegge's orchestration tools, Gas Town and Gas City, and mg supports them directly. That's a hint about where this whole stack is heading.

## Where this goes: Gas Town and Gas City

[Gas Town](https://github.com/gastownhall/gastown) is Yegge's multi-agent orchestrator built on the same Beads underneath, plus resident processes. When I asked how it fit, Claude's answer was that it's the fully built version of what we'd assembled by hand in an afternoon. Our effort bead is a convoy. The bookkeeping around each agent run is the Witness. Handing an issue to implementation is slinging to a polecat. Shepherding a PR to merge is the Refinery.

It's not for now, for three reasons:

- **It replaces the session model I work in.** I drive my sessions. Gas Town runs them.
- **It's built for unattended throughput**, twenty or thirty workers. My problem was visibility across a few dozen tmux windows I'm steering myself.
- **Practical friction:** a newer Beads than I run, and per-project databases instead of one shared one.

But the reason it's on the horizon at all goes back to the autonomy problem from the start of this post. Agents working from GitHub alone couldn't run unattended, because the blockers, the in-flight work in other chats and the decisions I'd made lived nowhere they could read. Beads changes that. The cross-cutting state is now written down, in a graph, where any agent can check what's blocked and what's ready before it touches anything. Gas Town is the part that acts on that graph without me in the loop.

Put together, that's something I couldn't honestly say before: if I wanted to, I could fire off a batch of work overnight and be more confident it would come out right than I would have been doing it half-supervised during the day. The agents wouldn't be guessing about the context. They'd be reading it.

What I'm watching for is the bottleneck moving. Right now it's me *understanding* where things are, and Beads fixes that. If in a few weeks the bottleneck has shifted to me *dispatching* work, if I find myself wishing efforts would advance while I sleep, that's the point to try Gas Town (or Gas City, which mg can also target) on one project. Nothing I've built would be thrown away. The beads carry over.

## What I learned

The main limit is the one Claude named on day one: the graph is only as good as the habit of adding steps to it. A work graph nobody updates is just a sadder wiki. That's why the updates happen at the start and end of every agent run, not by me remembering.

The bigger lesson is about layers. I went looking for one tool to fix "losing track," and the right answer was to notice it was three problems. A wiki can't know what's blocked. GitHub shouldn't hold my scratch state. A dashboard can only show what's already recorded somewhere. The missing piece was the boring middle: a private, agent-writable notebook that points at GitHub on one side and my memory on the other.

It's been running for a few days. Ask me in a month whether it survived contact with a real quarter.

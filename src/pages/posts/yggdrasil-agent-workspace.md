---
layout: ../../layouts/post.astro
title: 'My Agents Ask Each Other Before They Ask Me'
pubDate: 2026-11-27
description: 'Two months ago I gave my agents a shared notebook and said Gas Town was on the horizon. The horizon came early. My personal agent setup grew into Yggdrasil, a workspace my colleagues can install too. This post is about what it changed in how we work, not how it is built: I stopped being the scheduler, every developer''s instance talks to the others, and a question only reaches a human when no agent anywhere on the team can answer it.'
author: 'Torstein Skulbru'
excerpt: "I used to start every agent session, check on every agent session, and answer every question they had. The goal now is that nothing asks me anything. An agent figures it out itself, or asks a colleague's agents, and only comes to a person as a last resort."
image:
  src: '/images/yggdrasil-hero.webp'
  alt: 'A branching world tree connects many agent terminals to a single three-item decision list beside a seated person.'
tags: ['claude-code', 'ai', 'agents', 'gas-city', 'beads', 'developer-tools', 'workflow', 'productivity']
---

In my [last post](/posts/beads-local-shadow-for-agent-work) I wrote that the bottleneck in my agent work was me *understanding* where things were, and that Beads fixed it. I said I'd look at an orchestrator like Gas Town or Gas City once the bottleneck moved to me *dispatching* work.

It moved within two weeks.

With the blockers and decisions written down where agents could read them, I was the slowest part of the loop again, just in a new way. Every piece of work still waited for me to open a tmux window, start a Claude session, point it at the right issue, come back later to see whether it was stuck, and remember to push the PR through review. The agents could do the work. I was still the scheduler, the alarm clock and the memory.

This post is about what we built to get out of that role, and what it lets us do now. I'll mostly skip how it's built.

## The problem with being the scheduler

When you drive agents by hand, three things eat your day, and none of them is the actual work.

The first is starting things. Every issue, every review request and every failed CI run needs someone to notice it and kick off a session. If I'm in a meeting, nothing starts.

Then there's checking on things. A session that's waiting on a question looks like a session that's busy, until you switch to its window. With dozens of windows open, I spent a lot of time looking at agents that were fine, and missing the one that had been waiting on me for an hour.

![The "this is fine" dog sitting in a burning room, labelled "me in a meeting", while a sign on the wall reads "tmux window 47: agent waiting on a yes/no question for 58 minutes"](/images/yggdrasil-this-is-fine.webp)

And finally, finishing things. A PR isn't done when it's opened. It needs a review, fixes for the review, a green CI run, a rebase when main moves, and a nudge when a reviewer goes quiet. That's the least interesting part of the job and the easiest to forget.

So the goal wasn't "more agents." It was to have agents do the starting, checking and finishing themselves. And, eventually, the deciding too. Ideally nothing asks me anything. An agent that's stuck should figure it out on its own, from the code, the history and the work graph. If it can't, it should ask the agents of whoever knows that part of the system. A human is the last resort, not the first.

## Step one: a city of my own

I set up [Gas City](https://github.com/gastownhall/gascity), Steve Yegge's orchestrator, on top of Claude Code and the Beads graph from last time. The job description I wrote for it was short: watch GitHub, review the PRs I'm asked to review, ship the issues I hand over, babysit PRs to green, and "only bother you when a decision is genuinely yours."

That last line was the first version of the idea. It turned out to be too modest, but it was a start. The city runs a few standing roles: one that implements, one that reviews, one that watches operations, and an assistant I can talk to. They pick up work on their own. When one of them needs a human, because a design choice is ambiguous, a test can't be fixed without changing behaviour, or a merge needs a yes, it lands in one place.

That changed my day more than I expected. Work starts without me: I label an issue and it gets picked up, a review request comes in and a review gets written, a PR goes red and someone looks at it. Work finishes without me too. PRs get pushed to green and through the review gate, and one that has gone quiet for a week gets followed up instead of rotting. And instead of scanning windows to tell busy from waiting, I only look at what's waiting on me.

Nothing merges without passing review, and the gate can't be bypassed, by me or by an agent. Letting things run on their own only works if the guardrails don't depend on someone paying attention.

## Why not something off the shelf

Before building any of this, I spent a day looking at what already existed. There's no shortage of agent orchestrators, and I'd much rather use one than maintain one. I wrote down six things it had to do. It had to run locally next to all the tools and access our agents already use, drive Claude Code itself so our existing commands and plugins kept working, and handle work that spans several repos at once. It needed a hierarchy where escalations are checked before they reach a human, it had to pick up work from GitHub across the whole organisation, and it had to track work as a tree with dependencies.

No tool met all six. [Firstmate](https://github.com/kunchenguid/firstmate) came closest. It's local and tmux-based, it runs Claude Code, and it has the "escalate only real decisions" hierarchy I wanted, but nothing that picks up work from GitHub and no dependency tree. [Multica](https://github.com/multica-ai/multica) is polished and can be triggered by assigning an issue, but its lead routes work without vetting it, and one unit of work means one repo. Paperclip looked best on paper for org charts and governance, but it drives Claude Code through a generic adapter, so I doubted our commands would carry over. The cloud options, first-party ones included, couldn't reach the tools and systems our agents need. And the many session managers out there manage sessions, which was never my problem.

What I didn't want to write myself was the hardest part: keeping long-running Claude sessions alive, noticing when one is idle or stuck, and restarting it. Gas City does that. So the split was easy: borrow the orchestration, and build only the parts that are about how our team works.

## Step two: a last-resort list

The city worked, but it was a terminal UI that made sense to exactly one person. Colleagues asked for it, and that raised a question I'd never had to answer: what should this look like for someone who isn't me?

The answer became Yggdrasil, the world tree that connects everything. It's a desktop app, and its first screen isn't a list of agents or terminals. It's **Needs you**: a count at the top, then the items waiting on a human, with the PRs ready to merge right below.

That list is the last step of the escalation, and the number we're trying to drive to zero. I treat every row as a small bug report against the agents: why couldn't they work this out, and what would they have needed to know? Until the count is zero, you can act on each row right there:

- Answer it: open the agent's terminal from the row, answer its question, close it. The agent carries on, the count drops by one and the row is gone.
- Hand it back with a note, like "Go with option two, and add a test for the empty case." The agent takes it from there.
- Chat about it first, if you're not sure what you think yet.
- Take it over yourself. "Continue in Claude" drops you into a session with the context already loaded.

The rest of the app answers the other questions I used to keep in my head: what's being worked on right now, what's up next, and what happened while I was away. But the default view is the short list, and the goal is for it to be empty. On a good day it says "Nothing needs you," and that's true. The app tells "nothing needs you" apart from "I can't reach the agents right now," because a reassuring screen over a dead connection is worse than no screen.

## Teaching agents not to ask

If every row in that list is a bug report, the fix is rarely a smarter model. Almost every time I look at why an agent asked me something, the answer is that it was missing context I had: a decision made in a meeting, a reason a service is built the odd way it is, a customer constraint nobody wrote down, a "we tried that last year and it hurt."

So the habit I'm trying to build is to answer the question and then ask where the answer should have lived. Sometimes it belongs in the code as a comment, sometimes in the repo's docs, sometimes in the work graph from my last post, and sometimes in the memory the agents read at the start of every session. The answer goes in once, and the same question shouldn't reach me again, from that agent or any other.

It's slower than just typing "option two" and moving on. But every answer that only lives in my head is a question I'll be asked again next week, and every one that's written down is one the agents can settle without me. Over time, the list should get shorter because the agents know more. Letting them guess more would shorten it too, and that's the wrong way to get there.

## Step three: anyone can run it

The part I underestimated was how much of my setup only worked because I'd built it. I live in tmux, I know what a bead is, and I knew which of the moving parts was which. My colleagues shouldn't need any of that.

So a lot of the work went into making it something you can install and trust without learning how it works. It's one download, and the app walks you through signing in and connecting your repos. Every step shows the exact command it'll run, and you can change it if your machine is different.

Gas City has a wonderful vocabulary: cities, seats, convoys, slinging. None of it is in the UI, and a test fails if it creeps back in. People see "agents," "work" and "needs you." I'm also a keyboard person, and the first version showed it, so every action is now a visible button with the shortcut in the tooltip.

The agents act on GitHub as you, so a new install is deliberately timid. Agents start paused. Until you say otherwise, they review and answer, and never merge. The merge switch is off unless it's explicitly on, so a hiccup somewhere can't turn it on by accident. You raise the autonomy per repo when you're ready.

That matters more than any feature. People will only let agents work unattended if trying it costs nothing and nothing surprising happens. Paused by default and review-only by default mean the first hour is just watching what it would do.

## Step four: the laptop is just a window

Agents want an always-on machine with all the tools. People want to close their laptop and walk away. Those used to conflict: if the agents ran on my laptop, closing the lid stopped the work.

Now the agents can run on a machine that stays on, and the app on your laptop is a window onto it. In my words at the time: "a viewer mode … we dont want to have the data on the macbook." The work and the credentials stay on the engine. Close the lid in the office, open it at home or in a café, and the same Needs you list is waiting.

It sounds like a small thing. In practice it's the difference between agents that work while you're at your desk and agents that work while you sleep.

## Step five: from my agents to our agents

Every developer runs their own Yggdrasil, with their own agents, acting as them. On its own, that's just a lot of individual setups. What makes it a team tool is that the setups talk to each other. They form a mesh.

The instances know what the others are working on, so two people's agents don't end up doing the same thing, and nobody has to coordinate that in a chat thread. More importantly, agents ask each other before they ask people. When my agent is stuck on a part of the system a colleague knows better, the question doesn't go to me, and it doesn't go to my colleague either. It goes to their agents first, which know that part of the system the way my colleague's own setup does. Only if no agent can answer it does a person get asked, and then it's the right person, and the question arrives already researched.

![Doctor Octopus from Spider-Man 2 in close-up, one goggle lens glowing orange, captioned "the power of the mesh, in the palm of my hand"](/images/yggdrasil-power-of-the-sun.webp)

Some colleagues have been building agent work of their own in parallel, and it plugs into the same mesh. That's what moves agent work from "something one person on the team runs" to "something the team does." Nobody needs to know how it's wired to take part.

We're not all the way there, and how much the agents may settle among themselves is still switched on carefully, one step at a time. I'll write more once it has survived a few weeks of real use.

## Not tied to one vendor

Under all of this sits a decision I'd defend as hard as any feature: we don't want our way of working to live inside one vendor's product.

Every AI company now offers its own place to keep your setup: Claude Projects, cloud-hosted agents, custom GPTs and their equivalents. They're convenient, and each one is a small lock-in. Your prompts, your instructions and your workflows end up in someone else's UI, in someone else's format, tied to someone else's roadmap and pricing. Things move absurdly fast right now. The best model for a job today may not be the best one in three months, and the vendor that's ahead this quarter might not be next quarter. It's not unreasonable that we'll want an open-weight model like GLM or Qwen for some of the work down the line, or a mix: one model for implementing, another for security review, a third for a second opinion on PRs.

It isn't only the model vendors. There's a whole layer of third-party agent tools and wrappers between you and the models now, and the same applies to them. What they send home, how they handle a security problem, where the project goes when its owner loses interest or changes direction: none of that is yours to decide. That's a lot of trust to hand to a tool that sits between your agents and your code, holding your credentials. Running the vendors' own CLIs, with an orchestrator we can read and configuration we own, keeps that list short.

So the setup is built to keep that choice ours. The agents run the vendors' own command-line tools on our machines, not inside a hosted product, so we get each vendor's best work without moving in. Today that's Claude Code, and on purpose only Claude Code, because one harness done well beats three done badly. But choosing a different model per role has been a goal from the start, and swapping one out should mean changing a setting while the way we work stays the same.

The other half is sharing. The prompts, commands and review rules that decide how our agents behave live in a repo, versioned and reviewed like any other code. Everyone on the team gets the same set when they install, and there's room for personal additions on top. That works across everyone's own subscriptions and accounts, because the configuration lives in our repo and doesn't belong to any one account. When someone improves how agents review a PR, everyone gets the improvement, and if we switch models next year, all of that comes with us.

## What I'm still unsure about

A few things still keep me careful.

Confidently wrong is worse than stuck. An agent that asks me a question costs me a minute. An agent that should have asked, and didn't, can cost a day, or a customer's trust. Pushing questions away from humans only works if the agents are honest about what they don't know, and that's the property I trust least. Turning down the number of questions and turning up the number of quiet mistakes would be a bad trade.

Then there's the problem of agents agreeing with agents. When my agent asks a colleague's agent, it gets an answer from something that sounds just as sure of itself. Two agents can talk each other into a wrong answer as easily as two people can. Part of why autonomy is raised so slowly is that I don't yet know how often that happens.

They also act as you. Everything the agents do on GitHub is done in my name. If an agent merges something broken, I merged something broken. That's the right way for it to work, since someone has to be accountable, but it means an empty list isn't enough. I should understand what my agents did.

And I worry about whether people still learn. I've [written before](/posts/ai-junior-developers-learning-trap) about how agents can skip exactly the struggle that teaches people how a system works. A setup whose whole goal is to keep questions away from humans makes that sharper. A question that never reaches a junior developer is also something they never had to figure out. I don't have a good answer to this yet, beyond reading what the agents did and why.

## Where it is now

The city's first commit was about nine and a half weeks ago. The app is on its third minor release, colleagues are installing it and sending in fixes, and it runs on Linux and Mac.

Underneath, it's still mostly other people's work, on purpose. It runs the real Claude Code, so plugins, skills and subscriptions behave as they would in a terminal. The orchestration is Gas City, and the work graph is Beads. What we built is the part that fits it to how our team works.

![A variation of the "always has been" meme: one astronaut looking at Earth says "wait, it's all tmux underneath?", and the astronaut behind him gives a thumbs-up and says "always has been"](/images/yggdrasil-always-has-been.webp)

## What I learned

**Most of the work wasn't about agents.** The agents were the easy part, since someone else builds those. What took the time was everything around them: a setup anyone can get through, words anyone understands, defaults nobody has to be afraid of, and a screen that tells the truth when something is down. If only the builder can run it, it's a hobby.

**A question is missing context, not a missing feature.** When an agent asks a human, the fix is almost never a smarter model. It's writing down what the human knew, or letting the agent ask someone else's agents, who often know it already.

**Trust is granted in small steps.** Read-only before writes, review before merge, one repo before all of them.

**Own the parts that change slowly, rent the parts that change fast.** Models and vendors will keep leapfrogging each other. How our team works, what our agents are allowed to do and the rules they review by shouldn't have to move every time they do.

In the last post, the bottleneck was me understanding the work. Then it was me handing it out. Now it's me as the answer to questions some agent on the team could have answered. The goal is a Needs you list that stays empty, not because nothing is happening, but because the agents sorted it out among themselves. We're not there yet. For the first time, though, it feels like a reasonable thing to aim for.

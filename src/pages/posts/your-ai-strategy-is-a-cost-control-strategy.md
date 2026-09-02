---
layout: ../../layouts/post.astro
title: 'Your AI Strategy Is a Cost-Control Strategy'
pubDate: 2026-09-02
description: 'Token budgets, sandboxes, and who gets the frontier model. The three things leaders ask about most are the three signs a company is running AI as a cost centre. Here is what it looks like when the business runs on it instead.'
author: 'Torstein Skulbru'
isPinned: true
excerpt: 'Most companies are measuring AI by how little it costs. The ones pulling ahead are measuring it by how much of the company it can run.'
image:
  src: '/images/ai-cost-control-hero.webp'
  alt: 'Split office scene: on the left a manager padlocks an AI orb inside a glass box next to a usage meter, on the right one person works at a desk while AI orbs move freely around the room reading notes and diagrams'
tags: ['ai', 'leadership', 'business', 'strategy', 'llm', 'commentary']
blueskyUri: 'at://did:plc:rmnykyqh3zleost7ii4qe5nc/app.bsky.feed.post/3muknjrfk5s2p'
---

Nobody at my company thinks about what a token costs. Not the engineers. Not the people outside engineering who use the same tools. I do, once a month, when I open the dashboard. That is deliberate. It is closer to an AI strategy than most of what I hear described as one.

The conversations in leadership rooms run the other way. Someone asks what it costs. Someone asks whether it is safe to let it touch anything real. Someone points out that the best model is only available to a short list of approved companies, and we are not on it. Cost, containment, access. All reasonable questions. The order tells you what kind of company is asking.

A company that opens with cost, containment and access is running AI like a software licence: procure it, restrict it, keep the bill down. That is a cost-control strategy with an AI label. The companies pulling ahead treat AI as a layer the business runs on. They ask how much of the company it can carry.

Take the three in turn. They are the same mistake made three times.

## A meter buys you a cautious team

Here is how it goes. A company buys AI on pay-as-you-go pricing because that is how procurement buys cloud services. The bill arrives in "tokens", units of text sent to and returned by the model. Finance asks for a budget, and someone builds a dashboard showing who uses the most.

Picture the engineer who opens that dashboard and finds herself at the top. She will not walk into the CTO's office and argue that her usage is the company's most valuable, even if it is. She will trim: fewer questions, shorter ones, one approach instead of three. The invoice makes restraint visible; it never shows the output the team chose not to pursue. The dashboard did its job. It just had the wrong job.

The value does not come from the occasional careful question. It comes when people stop thinking about the cost of asking: they try five approaches in parallel and keep the best, have the assistant read the whole codebase instead of the one file that looks relevant, and leave a task running overnight to read the result in the morning. That is expensive by the meter and cheap by the outcome. A metered team learns not to do it.

I know because I measure it across engineers and non-engineers. Over the last thirty days, 18 people consumed just under 100 billion tokens. That was a slow month with holidays. At list prices, the usage would cost about $75,000. The heaviest user accounted for about $22,000. That person actually costs us a $200-a-month flat-rate seat, and the whole team's plans cost a small fraction of the metered figure.

The comparison is not perfectly fair. Most tokens are cached reads, when the assistant reuses context it has already seen, and vendors discount them steeply. List prices are not negotiated prices. But even if the real bill were a tenth of the estimate, the gap between what a flat-rate user consumes and what a metered user would dare to consume is the whole story. My most productive people run ten to thirty parallel sessions on a normal day without thinking about what one costs. That freedom is the product. The meter is what you are paying to remove.

I see the other side constantly. Large Norwegian companies route Claude and OpenAI through GitHub Copilot at close to per-token rates. They talk, sincerely, about using a lot of AI. Then you look at what "a lot" means. It is nowhere near what an unremarkable mid-sized company on flat-rate seats burns through in a normal week. Their people are not less capable. Every one of them is that engineer at the top of the dashboard, learning to look cheap. The company that talks most about AI and the company that uses the most of it are rarely the same company.

The elaborate version is the split setup: a frontier model on per-token billing for planning with starved context, then a free local model on the laptop for execution. Expensive brain, cheap hands. It fails twice. The frontier model plans from a thin brief because context costs money. Then the model least able to recover from a bad plan has to execute it. You economised on the part that needed the budget and spent on the part that did not. The saving is real. So is the mediocre result, and only one of them shows up on the invoice.

The vendors know this. GitHub, Cursor and OpenAI have all moved parts of their developer tooling from flat fees towards metered credits over the last eighteen months. Flat-rate plans still exist, and I will buy them for as long as they do. If your vendor only offers a meter, budget for the behaviour you want, not the behaviour you have.

## A sandbox is a symptom of rules nobody wrote down

The meter limits how much the assistant is used. The sandbox limits what it can touch. Put it in a sandbox, the argument goes. Give it a copy of the data, never the real thing. Let it suggest, never act.

I understand the impulse. An assistant that can read your production database and post in customer channels is a new kind of employee. You would not hand a new employee those keys on day one. But listen to what the sandbox says: we cannot express our rules to this thing, so we will keep it somewhere the rules do not matter. That is not a security posture. It is an admission that the rules were never written down.

The alternative is not "no rules". It is rules the assistant can read. Give it the access a trusted senior person would have and the constraints that person lives under: what it may see, what it may change, what needs human approval, and which parts of the business it must avoid. Write those rules as an onboarding document and put them where the assistant reads them every time it starts. None of that is exotic. It is the work of stating, plainly, how your company expects work to be done.

![A person holds an office door open and gestures toward a framed page of rules on the wall, welcoming a glowing AI orb in; behind them a filing cabinet with one drawer still padlocked, and an abandoned glass box on a far shelf](/images/ai-cost-control-rulebook.webp)

Do that and it can do work that matters. It can investigate a customer complaint end to end instead of summarising the ticket. It can take a well-described task, do it, and hand a finished change to a human for approval. It can brief you in the morning from your own calendar and open work. A sandboxed assistant does none of that, because none of it is possible without access.

The question for a leader is not "how do we contain it?" but "have we written our rules clearly enough to hand them to anyone?" If the answer is no, writing them is the work in front of you. The sandbox is not protecting you from the assistant. It is protecting you from doing that work.

## Nobody keeps the best model for long

The third conversation is about which model you may use at all. Anthropic's most capable model is available only to approved organisations and only in the United States. Similar tiers are forming at every vendor. Leaders conclude that the game is decided by who gets the best model, and that they are on the wrong side of the rope.

This is exactly backwards, and it is the most important point in this piece.

The same reflex appears quietly inside companies. Leadership decides that everyone will use one vendor's models because of an existing contract, a procurement relationship or a demo that went well, rarely because anyone tested the alternatives side by side on real work. The choice may be right on the day it is made. It is almost never right a month later. Major vendors ship new generations several times a year, the lead changes with each release, and models running on your own hardware have closed much of the gap. If you read this a month after I wrote it, your idea of the best model may not be mine, and neither of us is wrong. A mandate that names a vendor is a snapshot of a race dressed up as a strategy.

![Relay runners blurred mid-handover on a track, while in sharp focus in the foreground a hand holds a worn, string-bound notebook full of tabs, the only fully lit thing in the scene](/images/ai-cost-control-relay.webp)

Every company will end up with roughly the same models. Whatever is gated today becomes a public product soon enough, and whoever leads this quarter may trail the next. Model access is temporary; company knowledge is not. If your advantage depends on which model you are allowed to use, you do not have an advantage. You have a subscription.

What does not level out is what you have written down for the assistant: how your product works, the conventions your engineers follow, the playbooks for a support case, an outage or a release, who owns what, and the rules about what it may and may not touch. Written properly, that becomes a body of instructions any capable model can pick up and run. When a better one arrives, you swap it in and everything you encoded comes along. When you lose access to one, you swap it out and lose little.

That is the moat: the encoded company, which you own, not the model, which you rent. It is also the asset that compounds. Every problem solved with the assistant can become an instruction that makes the next one faster. A company that has done this for a year has an assistant that knows it deeply. Start next year with a better model and an empty page, and you still have a very smart new hire who knows nothing.

## Three questions that tell you which company you are

If you want to know whether your company runs AI as a cost centre or an operating system, three questions are enough.

**Does anyone in your company use it without thinking about the cost?** If everyone feels the meter, you are paying for a tool and getting a fraction of it. Move your heaviest users to flat-rate plans and tell them, explicitly, to be wasteful.

**Can the assistant do anything that matters?** If it can only suggest, summarise and draft, it is a good intern. If it can investigate, review, act and report inside written rules, it is a colleague. The difference is not the model. It is whether you wrote the rules.

**If your vendor disappeared tomorrow, what would you keep?** If the answer is "nothing; we would start again with a different vendor", you have built nothing. If it is "everything we taught it, running on a new model by Friday", you have.

Cost, containment and access are real concerns. I deal with all three. But they become the strategy when a company decides AI is something to buy and keep small. The companies I would bet on made the opposite decision. They decided AI is something the business runs on, then got to work writing down how that business runs.

Anyone can rent the model. Only you can write down your company.

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
---

Nobody at my company thinks about what a token costs. Not the engineers, not the people outside engineering who use the same tools. I do, once a month, when I open the dashboard. That is deliberate, and it is closer to an AI strategy than most of what I hear described as one.

I say that because the conversations in leadership rooms this year run the other way. Someone asks what it costs. Someone asks whether it is safe to let it touch anything real. Someone points out that the best model is only available to a short list of approved companies, and we are not on it. Cost, containment, access. Reasonable questions, all three, and the order they arrive in tells you what kind of company is asking.

A company that opens with cost, containment and access is running AI the way it runs a software licence: procure it, restrict it, keep the bill down. That is a cost-control strategy with an AI label on it. The companies pulling ahead treat AI as a layer the business runs on, and the questions they ask are about how much of the company it can carry.

Take the three in turn. They turn out to be the same mistake made three times.

## A meter buys you a cautious team

Here is how it usually goes. A company buys AI on pay-as-you-go pricing, because that is how procurement buys cloud things. The bill arrives in "tokens", roughly a count of words in and words out. Finance does not know what a token is, so it asks for a budget, and someone builds a dashboard showing who uses the most.

Picture the engineer who opens that dashboard and finds herself at the top of the list. She is not going to walk into the CTO's office and argue that her usage is the most valuable in the company, even if it is. She is going to trim: fewer questions, shorter ones, one approach instead of three. The dashboard did its job. It just had the wrong job.

The value of these tools does not come from the occasional careful question. It comes from a person who has stopped thinking about the cost of asking: who fires off five approaches to a problem in parallel and keeps the best one, who has the assistant read the whole codebase rather than the one file that seems relevant, who leaves a task running overnight and reads the result in the morning. All of that is expensive by the meter and cheap by the outcome, and a metered team learns not to do it.

I know the numbers because I measure them, engineers and non-engineers alike. Over the last thirty days, eighteen people consumed just under a hundred billion tokens. At list prices, that is about $75,000 for the month, and a slow month at that, with the tail end of summer holidays still thinning the team. Our heaviest user alone accounts for close to $22,000 of it. That person actually costs us a $200-a-month flat-rate seat, and the whole team's plans add up to a small fraction of the metered figure.

The comparison is not perfectly fair. Most of those tokens are the assistant re-reading context it has already seen, which vendors discount steeply, and list prices are not what a large customer pays. But even if the real bill were a tenth of the estimate, the gap between what a flat-rate user consumes and what a metered user would dare to consume is the whole story. My most productive people run ten to thirty parallel sessions on a normal day and have never once thought about what one of them costs. That freedom is the product. The meter is what you are paying to remove.

I see the other side of this constantly. Many large companies here in Norway have standardised on GitHub Copilot and route their Claude and OpenAI access through it, so every request is billed at close to the vendor's per-token rate. They talk, sincerely, about using a lot of AI. Then you look at what "a lot" means, and it is nowhere near what an unremarkable mid-sized company on flat-rate seats burns through in a normal week. Not because their people are less capable, but because every one of them is that engineer at the top of the dashboard. The company that talks most about AI and the company that uses the most of it are rarely the same company.

The elaborate version of the same instinct is the split setup: pay per token for a frontier model to do the thinking, then hand its plan to a small model running free on the developer's laptop to do the work. Expensive brain, cheap hands. It fails twice. The frontier model is starved of context, because context is what costs money, so it plans from a thin brief and the plan is only as good as the brief. Then the cheap local model, the one least able to recover from a bad plan, is the one that has to execute it. You have economised on the part that needed the budget and spent on the part that did not. The saving is real. So is the mediocre result, and only one of them shows up on the invoice.

The vendors know this, which is why GitHub, Cursor and OpenAI have all been moving parts of their developer tooling from flat fees toward metered credits over the last eighteen months. Flat-rate plans still exist, and I will buy them for as long as they do. If your vendor only offers a meter, budget for the behaviour you want, not the behaviour you have.

## A sandbox is a symptom of rules nobody wrote down

The meter limits how much the assistant is used. The sandbox limits what it is allowed to touch. Put it in a sandbox, the argument goes. Give it a copy of the data, never the real thing. Let it suggest but never act.

I understand the impulse. An assistant that can read your production database and post in your customer channels is a new kind of employee, and you would not hand a new employee those keys on day one. But listen to what the sandbox actually says: we have no way to express our rules to this thing, so we will keep it somewhere the rules do not matter. That is not a security posture. It is an admission that the rules were never written down.

The alternative is not "no rules". It is rules the assistant can read. Give it the access a trusted senior person would have, and the constraints that person lives under: what it may look at, what it may change, what needs a human signature, and which parts of the business it does not go near. Write those down as you would for an onboarding document, and put them where the assistant reads them every time it starts. None of that is exotic. It is the work of stating, plainly, how your company expects things to be done.

![A person holds an office door open and gestures toward a framed page of rules on the wall, welcoming a glowing AI orb in; behind them a filing cabinet with one drawer still padlocked, and an abandoned glass box on a far shelf](/images/ai-cost-control-rulebook.webp)

Do that and it can do work that matters. It can investigate a customer complaint from end to end instead of summarising the ticket. It can take a well-described task, do it, and hand a finished change to a human for approval. It can brief you in the morning from your own calendar and open work. A sandboxed assistant does none of that, because none of it is possible without access.

So the question for a leader is not "how do we contain it" but "have we written our rules down well enough that we could hand them to anyone". If the answer is no, that is the work. The sandbox is not protecting you from the assistant. It is protecting you from doing that work.

## Nobody keeps the best model for long

The third conversation is about which model you are allowed to use at all. Anthropic's most capable model is currently available only to a list of approved organisations, and only in the United States. Similar tiers are forming at every vendor. Leaders read this and conclude that the game is decided by who gets the best model, and that they are on the wrong side of the rope.

I think this is exactly backwards, and it is the most important point in this piece.

The same reflex shows up in a quieter form inside companies. The leadership team decides that everyone will use one vendor's models, on the strength of an existing contract, a procurement relationship or a demo that went well, and rarely because anyone ran the alternatives side by side on real work. Sometimes the choice is right on the day it is made. It is almost never right a month later. Every major vendor ships a new generation several times a year, the lead changes hands with each release, and the models you can run on your own hardware have closed most of the gap. If you are reading this a month after I wrote it, your idea of the best model is not the one I had in mind, and neither of us is wrong. A mandate that names a vendor is a snapshot of a race dressed up as a strategy.

![Relay runners blurred mid-handover on a track, while in sharp focus in the foreground a hand holds a worn, string-bound notebook full of tabs, the only fully lit thing in the scene](/images/ai-cost-control-relay.webp)

Every company will end up with roughly the same models. Whatever is gated today is a public product in a year, and whoever is ahead this quarter is behind the next. If your advantage depends on which model you are allowed to use, you do not have an advantage. You have a subscription.

What does not level out is everything you have written down for the assistant to use: how your product works, the conventions your engineers build by, the playbooks for a support case, an outage, a release, who owns what, and the rules about what it may and may not touch, the same rules that got it out of the sandbox. Written down properly, that is a body of instructions any capable model can pick up and run. When a better model arrives, you swap it in and everything you encoded comes along. When you lose access to one, you swap it out and lose very little.

That is the moat: the encoded company, which you own, not the model, which you rent. It is also the one asset that compounds. Every problem solved with the assistant becomes an instruction that makes the next one faster. A company that has been doing this for a year has an assistant that knows it deeply. A company that starts next year with a better model and an empty page has a very smart new hire who knows nothing.

## Three questions that tell you which company you are

If you want to know whether your company is running AI as a cost centre or as an operating system, three questions are enough.

**Does anyone in your company use it without thinking about the cost?** If everyone can feel the meter, you are paying for a tool and getting a fraction of it. Move your heaviest users to flat-rate plans and tell them, explicitly, that you want them to be wasteful.

**Can the assistant do anything that matters?** If it can only suggest, summarise and draft, it is a very good intern. If it can investigate, review, act and report inside rules you have written, it is a colleague. The difference is not the model. It is whether you wrote the rules.

**If your vendor disappeared tomorrow, what would you keep?** If the answer is "nothing, we would start again with a different vendor", you have not built anything yet. If the answer is "everything we taught it, running on a new model by Friday", you have.

Cost, containment and access are real concerns, and I deal with all three. But they are the concerns of a company that has decided AI is something to be bought and kept small. The companies I would bet on made the opposite decision. They decided it is something the business runs on, and then they got to work writing down how the business runs.

Anyone can rent the model. Only you can write down your company.

---
layout: ../../layouts/post.astro
title: 'Restoring Claude Code Sessions Into the Right tmux Window After a Reboot'
pubDate: 2026-06-05
description: 'tmux-resurrect brings your windows back, but every Claude Code pane comes back as a blank chat. Re-resuming the correct conversation into the correct window by hand is a tax I paid for months. Here is how tmux-assistant-resurrect closes the loop — and why my very first save came up empty.'
author: 'Torstein Skulbru'
isPinned: false
excerpt: "My layout survived every reboot. My Claude conversations did not — each pane came back as a fresh chat, and I'd spend ten minutes manually resuming this chat into that window. The fix is a tmux-resurrect companion, but the way it actually captures sessions surprised me."
image:
  src: '/images/tmux-assistant-resurrect-demo.gif'
  alt: 'Demo of tmux-assistant-resurrect saving and restoring assistant sessions across a tmux restart'
tags: ['claude-code', 'tmux', 'ai', 'developer-tools', 'linux', 'productivity', 'workflow']
---

I run a lot of Claude Code sessions, and I run them all inside tmux. On any given day I have a dozen windows open, each one a different project, each with a long-running Claude conversation that has built up real context — the kind you do not want to throw away. tmux-resurrect has handled the layout side of this for years: reboot the machine, press `prefix + Ctrl-r`, and my windows, panes, and working directories come right back.

Except the conversations did not. tmux-resurrect would faithfully reopen a pane in the right directory and relaunch `claude` — as a brand new, empty chat. The window was correct. The context was gone. So every reboot turned into a ten-minute scavenger hunt: `claude --resume`, scroll the picker, find the conversation that belonged to *this* window, repeat for every pane. Get it wrong and you are now reading the wrong project's history in the wrong window.

That tax finally annoyed me enough to fix it. This writeup is the result — partly a guide, partly a warning, because the tool works but the way it captures sessions is not what I assumed, and my first attempt produced an empty file that looked like a failure and was not.

## Why tmux-resurrect can't do this on its own

The core problem is structural. tmux-resurrect restores a program by remembering the **command line** that launched it. If a pane was running `vim foo.txt`, it can bring that back, because the file is right there in the process arguments. But a Claude Code conversation is identified by a session UUID, and that UUID **is not in the process arguments** unless you happened to launch with `claude --resume <id>` yourself. You almost never do — you just run `claude`.

So from the outside, every Claude pane looks identical: a `claude` process with no distinguishing args. tmux-resurrect has nothing to grab onto. It can restore the *binary*, not the *conversation*. There is an open request on the Claude Code repo to expose the session ID for exactly this reason, but until that lands, the gap has to be bridged some other way.

## The tool: tmux-assistant-resurrect

[`timvw/tmux-assistant-resurrect`](https://github.com/timvw/tmux-assistant-resurrect) is a companion plugin that hooks into tmux-resurrect's save and restore lifecycle. It handles Claude Code, OpenCode, and Codex CLI. Installation is the usual TPM dance — declare it **after** tmux-resurrect, since it piggybacks on resurrect's hooks:

```tmux
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'timvw/tmux-assistant-resurrect'
```

`prefix + I` to install. On save, it writes the discovered sessions to `assistant-sessions.json` next to tmux-resurrect's own save files. On restore, it reconstructs the full invocation — `claude --resume <id>`, plus any flags and environment it captured — and uses `send-keys` to type it into the matching pane. It is careful, too: before sending anything it checks the pane is sitting at a shell and not already running an assistant, so it never types into a live TUI or double-launches.

So far, so good. Then I saved, looked at the file, and it was empty.

## The part that surprised me: it's a hook, not a process scan

My first save produced this:

```json
{
  "timestamp": "2026-06-05T13:20:35Z",
  "sessions": []
}
```

Zero sessions. Every assumption I had about how this worked was wrong. I had pictured the save hook walking the process tree, finding `claude` processes, and somehow extracting their session IDs. That is not what happens — and it *cannot* be, because of the same args problem that defeats tmux-resurrect. The session ID is not visible from the process.

Instead, the plugin captures sessions through a **Claude Code `SessionStart` hook**. When you install the plugin via TPM, it wires a hook into your `~/.claude/settings.json`:

```json
"SessionStart": [
  {
    "matcher": "",
    "hooks": [
      { "type": "command",
        "command": "bash '.../hooks/claude-session-track.sh'" }
    ]
  }
]
```

When a Claude session **starts or resumes**, that hook fires. Claude hands it the session ID, the working directory, and a pile of metadata on stdin. The hook walks up the process tree to find the real `claude` PID (the hook itself is often spawned via an intermediate `sh -c`, so `$PPID` is not reliable), and writes a small state file — `claude-<pid>.json` — into a runtime directory, recording the session ID alongside `TMUX_PANE`. A matching `SessionEnd` hook deletes that file when the session closes.

The tmux save hook does not discover sessions. It just **reads those state files** and matches them to live panes. Which means the entire mechanism depends on the `SessionStart` hook having fired for a session at some point.

And there is the bug that was not a bug. Every Claude session I had open predated the moment I installed the plugin. The hook had never fired for any of them. There were no state files to read, so the save correctly reported nothing. The plumbing was perfect; it simply had nothing to capture yet.

Once I understood that, the behavior is obvious in hindsight:

- **New or resumed sessions are tracked automatically.** Start a chat, the hook fires, the state file appears. From that point on, every save picks it up.
- **Already-running sessions are invisible until they start or resume again.** The hook cannot retroactively reach back into a process that launched before it existed.

To back-fill the conversations I already had open, I quit each pane's TUI and relaunched with `claude --continue`, which resumes the *same* conversation and triggers `SessionStart` along the way — no context lost, and now the pane is tracked. One caveat: `--continue` grabs the most-recently-active chat for that directory, so if two panes live in the same repo, use `claude --resume` in the second and pick the right one explicitly. After that one-time migration, I never touch it again.

## Closing the loop with continuum

There was one more gap. I had tmux-resurrect but not [tmux-continuum](https://github.com/tmux-plugins/tmux-continuum), so my saves were manual. That is fine for layouts — but it defeats the whole point here. If I reboot without remembering to press `prefix + Ctrl-s` first, the last capture is stale and the session mapping is lost. The thing I was trying to automate was still leaning on me to remember a keystroke.

Three lines fixed it:

```tmux
set -g @plugin 'tmux-plugins/tmux-continuum'
set -g @continuum-save-interval '5'
set -g @continuum-restore 'on'
```

Now the environment auto-saves every five minutes and auto-restores when the tmux server starts. One ordering detail caught my eye in my own config: I set `status-right ''` early, and continuum drives its save loop by injecting a non-printing format into `status-right`. As long as TPM re-sources continuum *after* that line — which it does, since TPM initializes at the bottom of the config — the marker survives every reload. Worth checking if you blank out your status bar like I do.

## The steady state

The whole thing now behaves the way I wanted from the start:

1. I start or resume a Claude session in a tmux window. The `SessionStart` hook records it.
2. Continuum saves the environment every five minutes — layout plus the session mapping.
3. I reboot. On login, tmux-resurrect rebuilds the windows and panes, and tmux-assistant-resurrect types `claude --resume <id>` into each one.
4. Every window comes back with its own conversation, in its own directory, exactly where I left it.

The one rule to internalize: **a conversation is only captured from the moment it starts or resumes.** Everything downstream is automatic. The first time I rebooted after setting this up and watched a dozen windows quietly resume their own chats — no picker, no scavenger hunt — was genuinely the small kind of delightful that makes you wonder why you tolerated the manual version for so long.

If your layout already survives reboots but your AI conversations do not, this is an afternoon's worth of setup that pays itself back the first time the power blips.

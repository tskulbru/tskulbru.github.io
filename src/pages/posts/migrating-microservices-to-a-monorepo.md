---
layout: ../../layouts/post.astro
title: 'We Moved ~40 Microservices Into One Repo. Here Is What Happened.'
pubDate: 2026-04-03
description: 'A practical account of migrating ~40 Go microservices from individual GitHub repositories into a single monorepo using Go workspaces, path-filtered CI, and independent release management.'
author: 'Torstein Skulbru'
isPinned: false
excerpt: 'Forty repos, forty sets of CI configs, forty places to grep. We moved everything into one repo and most of the pain disappeared.'
image:
  src: '/images/portfolio/monorepo-hero.png'
  alt: 'Illustration of many small repositories merging into a single monorepo'
tags: ['go', 'monorepo', 'devops', 'microservices', 'architecture', 'ci-cd']
---

I was debugging a production issue that spanned three services. The request started in one API, triggered an event consumed by a second service, which wrote data picked up by a third. The bug was a field name mismatch introduced when someone updated a shared protobuf definition in one repo but forgot to regenerate the client in another.

Finding the root cause required cloning three repositories, cross-referencing three separate commit histories, and grepping across three `go.mod` files to figure out which version of the shared library each service was actually using. The fix was a one-line change. The investigation took most of a morning.

That was the moment I stopped thinking about whether we should consolidate our repositories and started thinking about how.

<img src="/images/portfolio/monorepo-hero.png" alt="Illustration of scattered repositories converging into a single unified monorepo" style="max-width: 100%; border-radius: 12px; margin: 1.5rem 0;" />

### The Multi-Repo Reality

We had roughly 40 Go microservices, each in its own GitHub repository. They had accumulated organically over a few years. Each new feature or domain got its own service, its own repo, its own CI pipeline, and its own deployment configuration.

On paper, this is the microservices dream. Independent deployability. Clear ownership boundaries. Small, focused codebases.

In practice, it created a different kind of complexity.

**Dependency drift was constant.** Shared libraries — things like tracing middleware, metrics helpers, and common data models — lived in their own repos too. When we updated the tracing library to support a new OpenTelemetry convention, we had to open pull requests in every service that consumed it. Some services would update immediately. Others would lag behind for weeks, sometimes months. At any given time, we had a dozen different versions of our own internal libraries running in production.

**Cross-service changes were painful.** Any feature that touched more than one service meant coordinating pull requests across multiple repos, reviewing them in the right order, and merging them in sequence. GitHub doesn't have a native concept of atomic cross-repo changes. We'd sometimes land the consumer side before the producer side and break staging for an hour.

**CI/CD configuration was duplicated everywhere.** Each repo had its own GitHub Actions workflow file. They were all slightly different — someone had updated the Go version in one but not the others, or added a linting step in some repos but not all. When we wanted to make a CI improvement (like adding golangci-lint), it was a tedious, multi-day campaign across every repo.

**Onboarding was slow.** A new team member joining the project needed to clone a dozen repos just to understand a single user-facing feature. "Which repo handles auth?" "Where does the event get published?" "Which service writes to that table?" The answers were scattered.

**Code review lacked context.** When reviewing a PR in the event consumer service, you couldn't easily see what the producer was actually sending without switching repos. You'd review code against an assumption about the contract, not the contract itself.

But the pain point that ultimately tipped the scale was something more fundamental.

**Our LLMs couldn't see the full picture.** This turned out to be the biggest reason we moved. Everyone on the team uses LLM-assisted coding tools daily — Claude Code, Copilot, Cursor. These tools are dramatically more useful when they can see the code they're reasoning about. With 40 separate repos, your LLM could only see the service you had open. It couldn't follow a request across service boundaries, couldn't check what the API actually returns when you're writing the consumer, couldn't trace a bug from the mobile app through the backend.

Once we moved to a monorepo, the difference was immediate. A mobile developer debugging why a feature is failing can point their LLM at the entire backend codebase. The LLM reads the API handler, checks the event consumer, looks at the data model — and tells you where the mismatch is. No context-switching, no "let me clone that other repo," no copy-pasting code snippets between chat sessions.

It goes beyond debugging. When a mobile developer is implementing a new feature that depends on a backend API, the LLM can read the actual endpoint implementation, understand the exact request/response shapes, and generate the client code correctly on the first try. It can even suggest features the developer hadn't considered by seeing what capabilities already exist in the backend. "This endpoint already supports filtering by date range — do you want to expose that in the UI?"

With multi-repo, the LLM is working with partial information at best. It's guessing at contracts, hallucinating field names, and suggesting implementations that don't match reality. With a monorepo, it has the full source of truth one `git pull` away.

This alone would have justified the migration. Everything else — the CI consolidation, the shared libraries, the atomic cross-service PRs — was a bonus.

<img src="/images/portfolio/monorepo-migration-flow.png" alt="Diagram showing the chaos of multi-repo microservices: tangled dependencies, duplicated CI, overwhelmed developer" style="max-width: 100%; border-radius: 12px; margin: 1.5rem 0;" />

### Why Not Just Fix Multi-Repo?

We considered it. Tools like Renovate can automate dependency bumps across repos. You can use a template repo for CI configuration. You can write scripts to coordinate cross-repo PRs.

But these are band-aids on a structural problem. The fundamental issue is that our services aren't actually independent. They share libraries, they share data contracts, they're deployed to the same cluster, and they're worked on by the same team. The repository boundaries were creating friction at every point of genuine collaboration.

A monorepo doesn't mean a monolith. The services would stay as separate deployable units, with their own binaries, their own Docker images, and their own release cycles. We'd just remove the artificial boundary that was making everyday development harder.

### The Migration Plan

We didn't do a big-bang migration. Instead, we moved services in batches over about two weeks, keeping both the old and new repos functional during the transition.

The plan was straightforward:

1. **Create the monorepo structure.** Set up the directory layout and Go workspace configuration.
2. **Move shared libraries first.** Get the `libs/` directory established so services could depend on it locally.
3. **Migrate services in batches.** Move 5-10 services at a time, starting with the ones that had the fewest external dependencies.
4. **Set up path-filtered CI.** Ensure that changes to one service only trigger builds for that service.
5. **Configure independent releases.** Each service keeps its own version and release cycle.
6. **Archive old repos.** Once everything was verified, archive the original repositories.

<img src="/images/portfolio/monorepo-libs-boundary.png" alt="Flowchart showing the six phases of migration from multi-repo to monorepo" style="max-width: 100%; border-radius: 12px; margin: 1.5rem 0;" />

### Preserving Git History

We didn't want to lose years of commit history. Every `git blame`, every bisect, every "why was this line changed?" answer lives in that history. Starting fresh would have been simpler, but it would have erased valuable context.

The approach: use `git filter-repo` to rewrite each service's history so that all files appear under their new subdirectory path, then merge each rewritten repo into the monorepo as a separate remote.

For each service repo, the process looked roughly like this:

```bash
# Clone the service repo
git clone git@github.com:org/service-a.git service-a-temp
cd service-a-temp

# Rewrite history so all files appear under services/apis/service-a/
git filter-repo --to-subdirectory-filter services/apis/service-a

# Back in the monorepo, add as a remote and merge
cd ../monorepo
git remote add service-a ../service-a-temp
git fetch service-a
git merge service-a/main --allow-unrelated-histories --no-edit
git remote remove service-a
```

After this, `git log -- services/apis/service-a/` shows the full original history of that service, and `git blame` works correctly on every file. The merge commits where each service joined the monorepo aren't pretty, but they're a one-time cost. We added a scripted wrapper (`migrate-repos.sh`) that automated this across all ~40 services so we didn't have to do it by hand.

**Tags needed restructuring.** In the old world, each repo had simple tags like `v1.4.2`. In a monorepo, that's ambiguous — version 1.4.2 of what? We adopted a namespaced tag convention: `service-name/v1.4.2`. This maps cleanly to Release Please's component-based versioning and to our CI pipeline triggers.

We didn't migrate old tags into the monorepo. Historical tags still exist in the archived original repos if anyone needs to reference them. Going forward, all new releases use the namespaced format. The production deployment workflow triggers on tags matching `flow-backend-*/v*.*.*`, extracts the service name from the tag, looks it up in the service registry, and deploys the correct Docker image.

```yaml
# Triggered by tags like: flow-backend-api-users/v2.1.0
on:
  push:
    tags:
      - 'flow-backend-*/v*.*.*'
```

This turned out to be cleaner than the old approach. One tagging convention, one deployment workflow, one place to look. Previously, each repo had its own slightly different release process — some used tags, some used branches, some were deployed manually. The migration forced us to standardize.

### Go Workspaces: The Key Enabler

Go 1.18 introduced workspaces, and they turned out to be the perfect tool for this migration. A `go.work` file at the root of the repo tells the Go toolchain to treat multiple modules as a single workspace:

```go
go 1.25

use (
    ./libs/metrics
    ./libs/tracing
    ./libs/models
    ./services/apis/service-a
    ./services/apis/service-b
    ./services/consumers/service-c
    // ... every module listed here
)
```

Each service keeps its own `go.mod` — it's still a proper Go module with its own dependency tree. But the workspace means that when service A imports the tracing library, Go resolves it to the local directory instead of fetching a tagged version from GitHub. **Changes to shared libraries are immediately visible to all services without publishing a new version.**

This was the single biggest improvement. Before: update library, tag release, wait for CI, open PRs in consuming services, wait for those CIs. After: update library, run tests across the workspace, open one PR.

We wrote a small script to auto-generate the `go.work` file by scanning for `go.mod` files in the repo. Anytime someone adds a new service, they run the script and the workspace updates.

```bash
#!/bin/bash
# generate-go-work.sh
echo "go 1.25" > go.work
echo "" >> go.work
echo "use (" >> go.work
find . -name "go.mod" -not -path "./go.mod" \
    | sed 's|/go.mod||' \
    | sort \
    | while read dir; do echo "    $dir" >> go.work; done
echo ")" >> go.work
```

### The Directory Structure

We landed on a categorized layout that reflects how the services actually operate:

```
monorepo/
├── services/
│   ├── apis/          # Request-response services (ConnectRPC)
│   ├── consumers/     # Event-driven message consumers
│   ├── cronjobs/      # Scheduled batch processing
│   └── jobs/          # One-time migration scripts
├── libs/              # Shared Go libraries
│   ├── metrics/       # Prometheus instrumentation
│   ├── tracing/       # OpenTelemetry middleware
│   └── models/        # Shared data structures
├── template/          # Dockerfile + boilerplate for new services
├── tests/             # End-to-end acceptance tests
├── scripts/           # Repo maintenance utilities
├── go.work            # Go workspace definition
└── Makefile           # Orchestration commands
```

The `services/` categorization isn't just cosmetic. APIs, consumers, and cronjobs have different operational characteristics — different scaling profiles, different monitoring needs, different failure modes. Grouping them this way makes it easy to apply category-wide policies.

The `template/` directory contains a Dockerfile and starter code for bootstrapping new services. Need a new consumer? Copy the template, add your business logic, run the workspace generator, and you're done. The Dockerfile uses multi-stage builds with a shared base configuration:

```dockerfile
FROM golang:${GO_VERSION}-alpine AS builder
WORKDIR /app
# Copy workspace-level files
COPY go.work go.work.sum ./
# Copy all module sources (Docker layer caching handles the rest)
COPY libs/ libs/
COPY services/ services/
# Build the specific service
RUN go build -o /service ./services/apis/my-service

FROM gcr.io/distroless/static-debian12
COPY --from=builder /service /service
ENTRYPOINT ["/service"]
```

The `distroless` base image keeps the final container tiny and reduces the attack surface. No shell, no package manager, just the binary.

### Path-Filtered CI: Only Build What Changed

This was the part I was most nervous about. In a monorepo, you can't run all tests on every PR — it would take forever and waste resources. You need CI that's smart about which services were actually affected by a change.

GitHub Actions has built-in path filtering, and it works well:

```yaml
on:
  pull_request:
    paths:
      - 'services/apis/service-a/**'
      - 'libs/**'

jobs:
  test-service-a:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version-file: 'services/apis/service-a/go.mod'
      - run: make test-service SERVICE=services/apis/service-a
```

But maintaining a separate workflow per service would just recreate the duplication problem. Instead, we use a dynamic matrix approach: a single workflow detects which services changed, then spawns build jobs only for those services.

**The critical detail: changes to `libs/` trigger builds for all services that depend on those libraries.** This catches the exact class of bug that motivated the migration in the first place — a shared library change that breaks a consumer.

A root `Makefile` provides uniform commands that work for any service:

```makefile
test-all:
    @for dir in $(shell find services -name "go.mod" -exec dirname {} \;); do \
        echo "Testing $$dir..."; \
        cd $$dir && go test ./... && cd $(ROOT); \
    done

lint-all:
    @golangci-lint run ./...
```

### Independent Releases With Release Please

One of the biggest concerns about monorepos is versioning. If everything is in one repo, does a single version number apply to everything? That would defeat the purpose of independent deployability.

We use [Release Please](https://github.com/googleapis/release-please), Google's release automation tool. It's designed for monorepos and supports per-component versioning out of the box.

Each service has its own entry in the Release Please configuration. When commits land on main, Release Please analyzes the conventional commit messages and opens separate release PRs for each affected service. Service A can be at v2.14.0 while service B is at v0.8.3. They evolve independently.

Tags follow the pattern `service-name/v1.2.3`, which triggers the production deployment workflow for that specific service. No other services are affected.

This gave us the best of both worlds: a single repo for development, independent release trains for deployment.

### The Service Registry

With 30 services in one repo, we needed a way to map between the directory structure and the deployment infrastructure. The service registry is a JSON file at the root of the repo that maps each service path to its Docker image name and Kubernetes metadata:

```json
{
  "services/apis/service-a": {
    "image": "registry.example.com/service-a",
    "deploy_target": "api-cluster"
  }
}
```

CI reads this file to know where to push the Docker image and which cluster to deploy to. It's a single source of truth that replaces the scattered deployment configs that used to live in each individual repo.

### Shared Libraries Done Right

The `libs/` directory contains three modules: metrics, tracing, and models. These are the things that genuinely need to be shared — cross-cutting infrastructure concerns that every service uses.

We were deliberate about what went into `libs/`. The temptation in a monorepo is to share everything. "Oh, service B has a nice retry helper, let's move it to libs." Resist this. Over-sharing creates tight coupling, which is exactly what microservices are supposed to avoid.

Our rules for `libs/`:

- **Infrastructure only.** Metrics, tracing, shared types — things that are about how services operate, not what they do.
- **No business logic.** If it encodes a business rule, it belongs in the service that owns that domain.
- **Stable interfaces.** Changes to `libs/` trigger builds across all services, so the API surface should be small and change infrequently.
- **Versioned within the workspace.** Services reference libs via the Go workspace, so there's no version number to manage. But we still write changelogs for significant changes.

### What Surprised Us

**Grep became powerful again.** Need to find every service that calls a specific function? `grep -r "FunctionName" services/`. Need to see every ConnectRPC endpoint in the system? One command. In multi-repo, this required cloning everything and writing a script. Now it's instant.

**Refactoring got dramatically easier.** When we renamed a field in a shared model, we could update every consumer in the same PR and verify everything compiled in one CI run. Before, this was a multi-day coordination exercise.

**PR reviews improved.** When a PR touches both the event producer and consumer, the reviewer sees both sides of the change. No more reviewing against assumptions.

**Go tooling just works.** `gopls` (the Go language server) understands workspaces natively. Jump-to-definition works across service boundaries. Find-all-references shows every consumer of a shared type. The IDE experience is significantly better than it was with separate repos.

**Build times were fine.** This was my biggest fear. Go's compilation is fast enough that even building all services from scratch takes under a minute. With Docker layer caching and the path-filtered CI, PR feedback loops stayed under 3 minutes.

### What Was Harder Than Expected

**Docker context size.** When the Dockerfile `COPY`s the entire workspace (all services and libs), the Docker build context is much larger than a single-service repo. We mitigated this with a `.dockerignore` that excludes everything except the target service and its dependencies, but getting the ignore patterns right took some iteration.

**IDE performance with many modules.** VS Code with 30+ Go modules in the workspace occasionally gets sluggish. `gopls` uses more memory and takes longer to initialize. It's manageable, but it's noticeably slower than opening a single-service repo. We set up a devcontainer configuration with tuned settings to help with this.

**People habits take time to change.** Developers who'd been working in isolated repos had muscle memory around `git clone <service>`, working in a small focused directory, and pushing changes without worrying about other services. The monorepo asks you to be aware of the broader system. PRs that touch shared libraries need more careful review. You need to think about whether your change affects other services, even if you're not modifying them directly.

### Linting At Scale

We use `golangci-lint` with a shared configuration at the repo root. This was another advantage of the monorepo — instead of each service having its own (often outdated) linting configuration, there's one `.golangci.yml` that applies everywhere.

The enabled linters include:

- **gosec** for security issues
- **errorlint** for proper error wrapping
- **cyclop** and **gocyclo** for complexity
- **dupl** for code duplication
- **goconst** for repeated string literals

Having consistent linting across all services raised the code quality baseline. Services that hadn't been linted in months suddenly had to meet the same standard as freshly written code. The initial cleanup was a bit of work, but it caught several genuine bugs — including an unchecked error return that could silently drop events.

### End-to-End Testing

The `tests/` directory at the root contains acceptance tests that exercise workflows spanning multiple services. These were technically possible with multi-repo, but practically nobody wrote them because the setup was so painful — you'd need to clone and run multiple services locally.

In the monorepo, a single `docker-compose` brings up the test dependencies (databases, message brokers), and the tests can import types from any service. We're still building this out, but even a handful of cross-service tests have already caught integration issues that unit tests in individual services would have missed.

### The Numbers

Here's a rough before and after:

| Metric | Multi-Repo | Monorepo |
|--------|-----------|----------|
| Repos to maintain | ~40 | 1 |
| CI config files | ~40 | 1 (with dynamic matrix) |
| Time to update shared library across all services | 1-2 days | 1 PR, same day |
| Time to onboard a new developer | Clone 10+ repos | Clone 1 repo |
| Cross-service PRs | Coordinated across repos | Single atomic PR |
| Dependency version drift | Common (weeks/months) | Eliminated |
| Grep across all services | Script + multiple clones | One command |

### When Multi-Repo Still Makes Sense

I don't think monorepos are universally better. They make sense when:

- A single team (or a small number of collaborating teams) owns the services
- Services share significant infrastructure code
- Cross-service changes are frequent
- You value code discovery and system-wide refactoring

Multi-repo makes more sense when:

- Services are owned by truly independent teams with different release cadences
- Services use different languages or build systems
- You need hard access control boundaries between services
- The services genuinely have no shared code

Our situation was clearly in the first camp. Same team, same language, shared libraries, frequent cross-cutting changes. The monorepo removed friction that was real and daily.

### Advice If You're Considering This

**Start with shared libraries.** Move your common code first and get the workspace working. This is the foundation everything else builds on.

**Invest in CI early.** Path-filtered builds aren't optional — they're required. Without them, every PR triggers 30 builds and developers will revolt.

**Keep services as independent modules.** Each service should have its own `go.mod` (or equivalent in your language). The monorepo is about co-location, not tight coupling.

**Don't over-share.** The temptation to move utilities into `libs/` is strong. Resist it. Share infrastructure, not business logic.

**Automate the boring stuff.** The workspace generator script, the service registry, the Dockerfile template — these small automations compound. Every new service should take 5 minutes to set up, not 50.

**Communicate the why.** The biggest resistance came from developers who associated monorepo with monolith. Be clear that the services remain independent — you're changing where the code lives, not how it's structured.

### Looking Back

The migration took about two weeks of focused work. There were a few rough days — the git history merge was fiddly, the Docker context issue burned an afternoon, and we had one exciting moment where a misconfigured CI workflow deployed the wrong service to staging.

But the daily developer experience improved immediately. The first time someone opened a PR that fixed a bug across two services with a single review cycle, it felt like we'd been carrying unnecessary weight for years.

Forty repos was not a scaling strategy. It was an accident of history — each service started small and independent, and by the time they were deeply interconnected, the repo structure was load-bearing. The monorepo migration was admitting that our architecture had evolved past the point where separate repos were helping.

If your microservices are worked on by the same people, share the same infrastructure, and are deployed to the same platform — they probably belong in the same repo. The repo boundary should reflect team boundaries, not service boundaries. Conway's Law runs in both directions.

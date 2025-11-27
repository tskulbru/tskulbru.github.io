---
layout: ../../layouts/post.astro
title: 'Scalable GitHub Release Management for Kubernetes with Shared Workflows'
pubDate: 2025-11-27
description: 'A practical guide to implementing multi-environment release management using GitHub Actions shared workflows, repository dispatch events, and GitOps patterns for Kubernetes deployments.'
author: 'Torstein Skulbru'
isPinned: true
excerpt: 'How to build a scalable CI/CD pipeline that connects multiple application repositories to a central Kubernetes configuration repository using shared workflows, repository dispatch events, and GitOps principles.'
image:
  src: '/images/github-k8s-release-header.png'
  alt: 'GitHub and Kubernetes connected through an automated release pipeline'
tags: ['kubernetes', 'github-actions', 'devops', 'gitops', 'ci-cd']
blueskyUri: ''
---

Managing releases across multiple microservices and Kubernetes environments gets messy fast. Every team ends up with slightly different CI/CD pipelines, inconsistent versioning, and no clear audit trail of what's deployed where.

After iterating on this problem across several projects, I've landed on a pattern that scales well: **shared GitHub workflows combined with repository dispatch events** that automatically update Kubernetes configurations. This creates a clean separation between application code and infrastructure configuration while maintaining full traceability.

Here's how it works.

## The Architecture

The pattern involves three components:

1. **Application repositories** - Each microservice has its own repo with minimal CI configuration
2. **Shared workflow repository** - Contains reusable GitHub Actions workflows for building and deploying
3. **Kubernetes configuration repository** - Holds all Kubernetes manifests, organized with Kustomize overlays

The flow is simple: when code is pushed to an application repo, it triggers the shared workflow. The workflow builds a container image, pushes it to a registry, then fires a dispatch event to the Kubernetes config repo. The config repo receives this event and automatically updates the deployment manifests with the new image tag.

> **Note:** While this post uses raw Kubernetes deployment manifests with Kustomize overlays for clarity and verbosity, this pattern works equally well with Helm. Instead of updating `deployment.yaml` files, your dispatch receiver workflow would update image tags in `values.yaml` files. The core concepts—shared workflows, repository dispatch events, and GitOps principles—remain exactly the same.

![Release management architecture showing the flow from application repository through shared workflow to Kubernetes config repository](/images/github-k8s-release-architecture.png)

## The Two-Tier Release Strategy

Most teams need different release strategies for development and production. Here's how to implement both:

### Development: Continuous Deployment on Main

Every push to `main` triggers an automatic deployment to the dev environment. This gives fast feedback loops and ensures developers always have a working environment to test against.

```yaml
# .github/workflows/dev-release-version.yaml
on:
  push:
    branches:
      - main

permissions:
  contents: write
  pull-requests: write

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.25'
      - name: Run unit tests
        run: go test -v -race -coverprofile=coverage.out -short ./...
      - name: Run e2e tests
        run: RUN_E2E_TESTS=1 go test -v -race -timeout 5m ./testing/e2e/...

  release-please:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: googleapis/release-please-action@v4
        with:
          token: ${{ secrets.GITHUB_PAT }}
          release-type: go

  deploy_dev:
    needs: [test, release-please]
    name: Deploy to dev
    uses: your-org/k8s-configurations/.github/workflows/reusable-acr-k8s-release-workflow.yaml@main
    secrets: inherit
    with:
      target_env: dev
      target_url: https://api.yourapp.dev
      config_root_folder: apps
      image_name: your-api-service
```

Notice the workflow does **two things in parallel** after tests pass:

1. **Deploys to dev** - Every push to main immediately builds and deploys to the dev environment
2. **Updates the Release Please PR** - Aggregates changes for the next production release

This dual behavior is key to the pattern. Developers get immediate feedback in dev, while production releases accumulate until you're ready to ship.

### Production: Tag-Based Releases

Production deployments are triggered by version tags. This gives you explicit control over what goes to production and creates a clear audit trail.

```yaml
# .github/workflows/prod-release-version.yaml
on:
  push:
    tags:
      - 'v*.*.*'
  workflow_dispatch:

concurrency:
  group: ${{ github.workflow }}-${{ github.ref || github.run_id }}
  cancel-in-progress: true

jobs:
  deploy_prod:
    name: Deploy to prod
    uses: your-org/k8s-configurations/.github/workflows/reusable-acr-k8s-release-workflow.yaml@main
    secrets: inherit
    with:
      target_env: prod
      target_url: https://api.yourapp.com
      config_root_folder: apps
      image_name: your-api-service
```

The `workflow_dispatch` trigger allows manual deployments when needed. The `concurrency` block prevents multiple simultaneous deployments to production.

## Automated Versioning with Release Please

The bridge between continuous dev deployments and controlled prod releases is [Release Please](https://github.com/googleapis/release-please), Google's release automation tool. It solves the "when do we release to production?" problem elegantly.

### How Release Please Works

Release Please watches your commits and automatically maintains a "release PR" that:

1. **Aggregates all changes** since the last release
2. **Generates a changelog** from conventional commit messages
3. **Bumps the version number** based on commit types (feat → minor, fix → patch, breaking change → major)
4. **Creates the git tag** when merged, which triggers your prod deployment

Here's the flow in practice:

![Release Please flow showing how commits trigger dev deployment and update the release PR, which when merged creates a tag and triggers production deployment](/images/github-k8s-release-please-flow.png)

### Conventional Commits Drive Everything

The version bumping is entirely automatic based on your commit messages:

```bash
# Patch release (1.2.3 → 1.2.4)
fix: resolve null pointer in user lookup
fix(api): handle empty response gracefully

# Minor release (1.2.3 → 1.3.0)
feat: add bulk user import
feat(export): support CSV format

# Major release (1.2.3 → 2.0.0)
feat!: redesign authentication flow
# or
feat: new auth system

BREAKING CHANGE: OAuth tokens from v1 are no longer valid
```

This means your release notes write themselves. No more "what changed since the last release?" meetings—just look at the PR.

### The Release PR as a Gate

The Release Please PR becomes your production gate. It accumulates changes as developers merge to main, each merge triggering a dev deployment and updating the PR. When you're ready for production:

1. Review the accumulated changelog
2. Merge the Release Please PR
3. Release Please automatically creates the version tag
4. The tag triggers your production deployment workflow

This gives you the best of both worlds: continuous deployment to dev for fast iteration, and explicit control over production releases with full visibility into what's shipping.

### Configuration

Release Please needs minimal configuration. Add a `release-please-config.json` to your repo:

```json
{
	"$schema": "https://raw.githubusercontent.com/googleapis/release-please/main/schemas/config.json",
	"release-type": "go",
	"bump-minor-pre-major": true,
	"bump-patch-for-minor-pre-major": true,
	"include-component-in-tag": false,
	"packages": {
		".": {}
	}
}
```

And a `.release-please-manifest.json` to track the current version:

```json
{
	".": "1.2.3"
}
```

Release Please supports many release types (`go`, `node`, `python`, `rust`, etc.) and handles language-specific version files automatically (package.json, pyproject.toml, Cargo.toml, etc.).

## The Shared Workflow

This is the heart of the system. A single reusable workflow handles building, pushing, and triggering deployments for all your services.

```yaml
# .github/workflows/reusable-acr-k8s-release-workflow.yaml
on:
  workflow_call:
    inputs:
      target_env:
        description: 'The target environment [prod,dev]'
        type: string
        default: 'dev'
        required: true
      image_name:
        description: 'The name of the image to build and push'
        type: string
        required: true
      config_root_folder:
        description: 'The config root folder for k8s configs'
        type: string
        required: true
      target_url:
        description: 'The target URL for the deployment environment'
        type: string
        required: false
      target_k8s_image_kind:
        description: 'The kind of K8s manifest [new-image, new-job-image]'
        type: string
        default: 'new-image'
        required: false
      docker_file:
        description: 'Path to the Dockerfile'
        required: false
        type: string
        default: './Dockerfile'
      docker_context:
        description: 'Docker build context'
        required: false
        type: string
        default: '.'

jobs:
  build-and-deploy:
    name: Build container image
    runs-on: ubuntu-latest
    environment:
      name: ${{ inputs.target_env }}
      url: ${{ inputs.target_url }}
    steps:
      - name: Validate target_env
        run: |
          if ! [[ "${{ inputs.target_env }}" =~ ^(prod|dev)$ ]]; then
            echo "Validation Failed: target_env must be 'prod' or 'dev'."
            exit 1
          fi

      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Docker meta
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: |
            ${{ secrets.CR_ENDPOINT }}/${{ inputs.image_name }}
          tags: |
            type=semver,pattern={{raw}}
            type=raw,value={{date 'YYYYMMDDHHmmssSSS'}}

      - name: Set up QEMU
        uses: docker/setup-qemu-action@v3

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log into registry
        uses: docker/login-action@v3
        with:
          registry: ${{ secrets.CR_ENDPOINT }}
          username: ${{ secrets.CR_USERNAME }}
          password: ${{ secrets.CR_PASSWORD }}

      - name: Build & Push Docker Image
        uses: docker/build-push-action@v5
        with:
          context: ${{ inputs.docker_context }}
          file: ${{ inputs.docker_file }}
          push: true
          platforms: linux/amd64,linux/arm64
          build-args: |
            version=${{ steps.meta.outputs.version }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=registry,ref=${{ secrets.CR_ENDPOINT }}/${{ inputs.image_name }}
          cache-to: type=inline

      - name: Repository Dispatch to Update Configurations
        if: success()
        uses: peter-evans/repository-dispatch@v3
        with:
          token: ${{ secrets.GITHUB_PAT }}
          repository: your-org/k8s-configurations
          event-type: ${{ inputs.target_k8s_image_kind }}
          client-payload: >-
            {
              "image": "${{ secrets.CR_ENDPOINT }}/${{ inputs.image_name }}:${{ steps.meta.outputs.version }}",
              "release": "${{ inputs.image_name }}@${{ steps.meta.outputs.version }}",
              "path": "${{ inputs.config_root_folder }}/${{ inputs.image_name }}/overlays/${{ inputs.target_env }}"
            }
```

Key features of this workflow:

- **Multi-architecture builds** - Supports both amd64 and arm64 for flexibility
- **Smart tagging** - Uses semantic version tags for releases and timestamps for dev builds
- **Registry caching** - Significantly speeds up subsequent builds
- **Environment URLs** - GitHub shows deployment status with direct links to the deployed service
- **Dispatch payload** - Contains everything the config repo needs to update the right files

## Cross-Repository Communication

The magic happens with `repository_dispatch`. When the shared workflow finishes building, it fires an event to the Kubernetes config repository with a structured payload:

```json
{
	"image": "yourregistry.io/your-api-service:v1.2.3",
	"release": "your-api-service@v1.2.3",
	"path": "apps/your-api-service/overlays/prod"
}
```

The config repository listens for these events and automatically updates the Kubernetes manifests:

```yaml
# .github/workflows/app-image-update.yaml
name: App Image Update

on:
  repository_dispatch:
    types: [new-image]

jobs:
  update-deployment:
    runs-on: ubuntu-latest
    permissions:
      contents: write

    steps:
      - uses: actions/checkout@v4

      - name: Update Image Version
        uses: mikefarah/yq@master
        with:
          cmd: >-
            yq eval '
              .spec.template.spec.containers[0].image = "${{ github.event.client_payload.image }}" |
              .spec.template.spec.containers[0].env[0].value = "${{ github.event.client_payload.release }}"
            ' -i ${{ github.event.client_payload.path }}/deployment.yaml

      - name: Update Related Overlays
        run: |
          APP_PATH=$(dirname "${{ github.event.client_payload.path }}")
          OVERLAY_NAME=$(basename "${{ github.event.client_payload.path }}")

          # For prod deployments, also update any prod-* variants (prod-eu, prod-us, etc.)
          if [[ "$OVERLAY_NAME" == "prod" ]]; then
            for overlay_dir in "$APP_PATH"/prod-*; do
              if [[ -d "$overlay_dir" && -f "$overlay_dir/deployment.yaml" ]]; then
                echo "Updating related overlay: $overlay_dir"
                yq eval '
                  .spec.template.spec.containers[0].image = "${{ github.event.client_payload.image }}" |
                  .spec.template.spec.containers[0].env[0].value = "${{ github.event.client_payload.release }}"
                ' -i "$overlay_dir/deployment.yaml"
              fi
            done
          fi

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add .
          git commit -m "Deploy ${{ github.event.client_payload.release }}"
          git pull --rebase
          git push
```

This approach has a nice property: **every deployment is a git commit**. You can see exactly what changed, when, and why. Rolling back is just reverting a commit.

## Kubernetes Configuration Structure

The config repository uses Kustomize overlays to manage environment-specific configurations:

```
k8s-configurations/
├── apps/
│   ├── your-api-service/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   ├── ingress.yaml
│   │   │   ├── hpa.yaml
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── dev/
│   │       │   ├── deployment.yaml
│   │       │   └── kustomization.yaml
│   │       ├── prod/
│   │       │   ├── deployment.yaml
│   │       │   └── kustomization.yaml
│   │       └── prod-eu/
│   │           ├── deployment.yaml
│   │           └── kustomization.yaml
│   └── another-service/
│       └── ...
└── .github/
    └── workflows/
        ├── app-image-update.yaml
        ├── cronjob-image-update.yaml
        └── reusable-acr-k8s-release-workflow.yaml
```

The overlay deployment files contain only the fields that differ from the base:

```yaml
# overlays/prod/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: your-api-service
spec:
  template:
    metadata:
      labels:
        environment: prod
    spec:
      containers:
        - name: your-api-service
          image: yourregistry.io/your-api-service:v1.2.3
          env:
            - name: APP_RELEASEVERSION
              value: your-api-service@v1.2.3
```

The `APP_RELEASEVERSION` environment variable is useful for logging, metrics, and debugging—you always know exactly which version is running.

## Handling Different Workload Types

Not everything is a standard deployment. CronJobs and other workload types need different update logic:

```yaml
# .github/workflows/cronjob-image-update.yaml
name: CronJob Image Update

on:
  repository_dispatch:
    types: [new-job-image]

jobs:
  update-cronjob:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Update Image Version
        uses: mikefarah/yq@master
        with:
          cmd: >-
            yq eval '
              .spec.jobTemplate.spec.template.spec.containers[0].image = "${{ github.event.client_payload.image }}" |
              .spec.jobTemplate.spec.template.spec.containers[0].env[0].value = "${{ github.event.client_payload.release }}"
            ' -i ${{ github.event.client_payload.path }}/cronjob.yaml

      - name: Commit and push
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
          git add .
          git commit -m "Deploy cronjob ${{ github.event.client_payload.release }}"
          git pull --rebase
          git push
```

Application repos can specify which event type to use via the `target_k8s_image_kind` input parameter.

## Connecting to GitOps Tools

The config repository becomes the single source of truth for what should be deployed. From here, you have two options:

**Option 1: Direct deployment from GitHub Actions**

Add a final step to the image update workflows that applies the changes directly:

```yaml
- name: Deploy to cluster
  run: |
    kubectl apply -k ${{ github.event.client_payload.path }}
```

**Option 2: GitOps with ArgoCD or Flux**

Point your GitOps tool at the config repository. Every commit triggers automatic synchronization to the cluster. This is my preferred approach because it provides:

- Drift detection between git and cluster state
- Automatic rollback on failed deployments
- A clear separation between "what should be deployed" and "how it gets deployed"

ArgoCD configuration example:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: your-api-service-prod
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/your-org/k8s-configurations.git
    targetRevision: main
    path: apps/your-api-service/overlays/prod
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Optional: Blue/Green Deployments with Argo Rollouts

For production environments where zero-downtime deployments are critical, you can extend this pattern with [Argo Rollouts](https://argoproj.github.io/rollouts/). Rollouts replaces the standard Kubernetes Deployment with a more sophisticated controller that supports blue/green and canary deployment strategies.

### Why Blue/Green?

Standard Kubernetes deployments use a rolling update strategy—pods are replaced gradually. This works well for most cases, but has limitations:

- **No instant rollback** - If the new version has issues, you're waiting for pods to terminate and restart
- **Mixed traffic during rollout** - Users might hit both old and new versions simultaneously
- **No pre-flight validation** - New pods serve traffic as soon as they're ready

Blue/green deployments solve this by running two complete environments:

![Blue/Green deployment architecture showing load balancer routing traffic to the active Blue environment while Green environment is ready for testing](/images/github-k8s-blue-green-deployment.png)

The new version (green) is fully deployed and validated before receiving any production traffic. When you're confident it works, traffic switches instantly. If something goes wrong, switching back is equally instant.

### Integrating Argo Rollouts

Argo Rollouts works seamlessly with the GitOps pattern. Instead of a Deployment, you define a Rollout resource in your config repo:

```yaml
# base/rollout.yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: your-api-service
spec:
  replicas: 3
  revisionHistoryLimit: 3
  selector:
    matchLabels:
      app: your-api-service
  template:
    metadata:
      labels:
        app: your-api-service
    spec:
      containers:
        - name: your-api-service
          image: yourregistry.io/your-api-service:v1.2.3
          ports:
            - containerPort: 8080
          env:
            - name: APP_RELEASEVERSION
              value: your-api-service@v1.2.3
          readinessProbe:
            httpGet:
              path: /health
              port: 8080
            initialDelaySeconds: 5
            periodSeconds: 5
  strategy:
    blueGreen:
      activeService: your-api-service-active
      previewService: your-api-service-preview
      autoPromotionEnabled: false
      previewReplicaCount: 3
      scaleDownDelaySeconds: 30
```

The key configuration is in the `strategy.blueGreen` section:

- **activeService** - The service receiving production traffic
- **previewService** - The service pointing to the new version for testing
- **autoPromotionEnabled: false** - Requires manual promotion (or automated testing)
- **previewReplicaCount** - How many replicas to run for the preview
- **scaleDownDelaySeconds** - How long to keep the old version after switching

You'll also need two services:

```yaml
# base/service-active.yaml
apiVersion: v1
kind: Service
metadata:
  name: your-api-service-active
spec:
  selector:
    app: your-api-service
  ports:
    - port: 80
      targetPort: 8080
---
# base/service-preview.yaml
apiVersion: v1
kind: Service
metadata:
  name: your-api-service-preview
spec:
  selector:
    app: your-api-service
  ports:
    - port: 80
      targetPort: 8080
```

Argo Rollouts automatically manages which ReplicaSet each service points to.

### The Deployment Flow with Rollouts

When the dispatch event updates the image in your Rollout manifest:

1. **ArgoCD detects the change** and syncs the new Rollout spec
2. **Argo Rollouts creates a new ReplicaSet** with the new image
3. **Preview service switches** to the new ReplicaSet
4. **New version is fully deployed** but receives no production traffic
5. **Team validates** via the preview service endpoint
6. **Manual promotion** (or automated analysis) switches traffic
7. **Old ReplicaSet scales down** after the delay period

![Argo Rollouts deployment timeline showing stages from image update through preview, validation, promotion, and cleanup](/images/github-k8s-rollout-timeline.png)

### Promotion Options

You can promote the new version in several ways:

**Manual promotion via kubectl:**

```bash
kubectl argo rollouts promote your-api-service -n production
```

**Via the Argo Rollouts dashboard:**
Argo Rollouts includes a web UI for visualizing and managing rollouts.

**Automated via AnalysisTemplate:**
Define success criteria that automatically promote (or rollback) based on metrics:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  metrics:
    - name: success-rate
      interval: 1m
      count: 5
      successCondition: result[0] >= 0.95
      failureLimit: 3
      provider:
        prometheus:
          address: http://prometheus.monitoring:9090
          query: |
            sum(rate(http_requests_total{service="your-api-service-preview",status=~"2.."}[5m]))
            /
            sum(rate(http_requests_total{service="your-api-service-preview"}[5m]))
```

Reference this in your Rollout:

```yaml
strategy:
  blueGreen:
    activeService: your-api-service-active
    previewService: your-api-service-preview
    autoPromotionEnabled: true
    prePromotionAnalysis:
      templates:
        - templateName: success-rate
```

### Updating the Dispatch Workflow

The image update workflow needs a small modification to handle Rollouts:

```yaml
- name: Update Image Version
  uses: mikefarah/yq@master
  with:
    cmd: >-
      yq eval '
        .spec.template.spec.containers[0].image = "${{ github.event.client_payload.image }}" |
        .spec.template.spec.containers[0].env[0].value = "${{ github.event.client_payload.release }}"
      ' -i ${{ github.event.client_payload.path }}/rollout.yaml
```

The only change is the filename (`rollout.yaml` instead of `deployment.yaml`). The YAML structure is identical, so the same yq command works.

### When to Use Blue/Green

Blue/green deployments add operational complexity. Consider them when:

- **Zero-downtime is critical** - Financial services, real-time systems
- **You need instant rollback** - User-facing production services
- **Pre-production validation is required** - Compliance or regulated environments
- **Database migrations are involved** - Test the new version against production data before switching

For dev environments or services where brief mixed-version traffic is acceptable, standard rolling deployments are simpler and sufficient.

## Why This Pattern Works

After using this approach across multiple projects, here's what I've found valuable:

**Consistency across services** - Every microservice uses the same deployment process. New services get CI/CD by adding two small workflow files.

**Clear separation of concerns** - Application repos own their code and tests. The config repo owns infrastructure concerns. Neither needs to know the implementation details of the other.

**Full audit trail** - Every deployment is a git commit. You can answer "what was deployed to production on Tuesday?" by looking at git history.

**Self-documenting releases** - Release Please generates changelogs automatically from conventional commits. Release notes write themselves, and the Release PR shows exactly what's shipping to production.

**Controlled production releases** - Dev gets continuous deployment for fast feedback, but production requires explicit action (merging the Release PR). No accidental production deployments.

**Easy rollbacks** - Revert a commit in the config repo to roll back a deployment. No need to rebuild containers or re-run pipelines.

**Scalable secrets management** - Secrets are configured once at the organization level and inherited via `secrets: inherit`. No need to configure them per-repository.

**Multi-environment support** - Adding a new environment (staging, prod-eu, etc.) is just adding a new overlay directory.

## Common Pitfalls

**Race conditions on concurrent deployments** - If two services deploy simultaneously, the config repo updates can conflict. The `git pull --rebase` in the update workflow handles most cases, but consider adding concurrency controls for high-volume deployments.

**Secret sprawl** - Organization-level secrets simplify management but can grow unwieldy. Document which secrets are used and audit regularly.

**Debugging dispatch failures** - Repository dispatch events don't show up in the calling workflow's logs. Add explicit logging in your dispatch receiver workflows and consider using GitHub's webhook delivery logs for debugging.

**Drift between environments** - Dev gets every commit, but prod only gets tagged releases. This is intentional, but make sure your team understands the implications and has a regular release cadence.

## Getting Started

To implement this pattern:

1. Create a Kubernetes configuration repository with your manifests organized in Kustomize overlays
2. Add the shared workflow and dispatch receiver workflows to the config repo
3. Configure organization-level secrets for registry credentials and a GitHub PAT with repo access
4. Update application repos to call the shared workflow instead of their own deployment logic

Start with a single service to validate the pattern, then migrate others incrementally. The consistency gains compound as you add more services.

---

_This pattern has been running in production across multiple microservices for years. The initial setup takes some effort, but the operational simplicity pays dividends as your system grows._

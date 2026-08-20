# Renter 🏠 — Cloud-Native Rental Platform on AWS EKS

A production-grade rental-listing platform deployed on **AWS EKS** with **Terraform**, **ArgoCD GitOps**, and a full **Prometheus / Grafana / Loki** observability stack.

Anyone can browse published houses and apartments without logging in — photos and location are public, but the owner's contact info stays hidden until you sign in. Listings from unverified users go through a moderation queue before publishing.

The application itself is Django (DRF + JWT API, server-rendered templates, Celery workers) — but the main focus of this project is the **infrastructure, CI/CD, and GitOps delivery pipeline** around it.

## The three repos

| Repo | Role |
| --- | --- |
| [`renter`](https://github.com/aryalsaurav/renter) (this repo) | Django application, Dockerfiles, GitHub Actions CI/CD, and the application **Helm chart** (`k8s/`) that ArgoCD deploys |
| [`renter-terraform`](https://github.com/aryalsaurav/renter-terraform) | **Terraform** — modular IaC for the entire AWS footprint: VPC, EKS, RDS, ElastiCache, ECR, S3, IAM, security groups, Secrets Manager, plus the ArgoCD Helm release that bootstraps GitOps |
| [`renter-infra`](https://github.com/aryalsaurav/renter-infra) | **GitOps source of truth** — ArgoCD app-of-apps: platform add-ons (ingress-nginx, cert-manager, external-secrets, storage) and the monitoring stack (kube-prometheus-stack, Loki, Alloy) |

## Architecture

```
                        ┌─────────────────────────────────────────────────┐
                        │                   AWS (Terraform)               │
                        │                                                 │
  GitHub Actions ──────▶│  ECR ◀── image push (OIDC, no static keys)      │
   (CI/CD, OIDC)        │                                                 │
        │               │  ┌───────────────── EKS ─────────────────────┐  │
        │ yq bumps      │  │                                            │  │
        │ Helm values   │  │  ArgoCD ── app-of-apps ── renter-infra     │  │
        ▼               │  │    │                                       │  │
  renter repo ─────────▶│  │    ├─ ingress-nginx ── cert-manager (ACME) │  │
  (k8s/ Helm chart)     │  │    ├─ external-secrets ── Secrets Manager  │  │
                        │  │    ├─ kube-prometheus-stack (Grafana)      │  │
                        │  │    ├─ Loki + Alloy (logs, DaemonSet)       │  │
                        │  │    └─ renter app (API, Celery, HPA, Jobs)  │  │
                        │  └────────────────────────────────────────────┘  │
                        │                                                 │
                        │  RDS PostgreSQL   ElastiCache Redis   S3        │
                        └─────────────────────────────────────────────────┘
```

## Infrastructure — `renter-terraform`

Modular Terraform with per-environment roots (`environments/dev`) composing reusable modules:

- **`vpc`** — public/private subnets, single NAT gateway for cost control
- **`eks`** — EKS cluster with `API` authentication mode, access entries instead of `aws-auth`, managed node group behind a custom launch template, core add-ons incl. the `eks-pod-identity-agent`, and **Pod Identity associations** binding IAM roles to the EBS CSI, External Secrets, and app service accounts
- **`iam`** — least-privilege roles for cluster, nodes, EBS CSI, External Secrets (EKS Pod Identity), S3 access, and a **GitHub OIDC deploy role** scoped to `repo:<org>/<repo>:ref:refs/heads/main` so CI never holds long-lived AWS keys
- **`databases`** — RDS PostgreSQL (managed master-user secret, multi-AZ/backup/deletion-protection toggles) and ElastiCache Redis replication group
- **`ecr`**, **`s3`**, **`secrets`**, **`security`** — image registry, media bucket, application secret in Secrets Manager, and security groups wiring EKS nodes ⇄ RDS ⇄ Redis

Terraform also installs **ArgoCD via the Helm provider** as the last step — after `terraform apply`, one `kubectl apply` of the root Application bootstraps everything else.

## GitOps — `renter-infra`

ArgoCD **app-of-apps**: a single root `Application` points at `argocd/applications/`, and every platform component is itself an ArgoCD `Application` with automated sync (`prune` + `selfHeal`):

- **`ingress-nginx`** — cluster ingress, plus Ingress objects for ArgoCD and Grafana
- **`cert-manager`** — Let's Encrypt staging + prod `ClusterIssuer`s (HTTP-01)
- **`external-secrets`** — External Secrets Operator with a `ClusterSecretStore` backed by **AWS Secrets Manager** (auth via EKS Pod Identity); the app's `ExternalSecret` pulls the RDS master-user secret and application secrets into the cluster with a 1h refresh
- **`storage`** — default **gp3** StorageClass
- **`kube-prometheus-stack`** — Prometheus (15d retention, 20Gi gp3 PVC) + **Grafana** (persistent dashboards)
- **`loki` + `alloy`** — Loki single-binary with retention/compaction configured, and Grafana **Alloy as a DaemonSet** discovering and relabeling pod logs cluster-wide
- **`renter`** — the application itself, deployed from the Helm chart in the `renter` repo with `values.yaml` + `values-prod.yaml`

## Application deployment — `renter/k8s`

The Helm chart deploys the API and Celery workers with production concerns handled in-chart:

- **Sync-wave ordering** — ServiceAccount/secrets (wave −1) → **migration Job** (wave 0, `BeforeHookCreation` delete policy) → deployments → HPA (wave 2), so migrations always run before new pods roll
- **HPA** on CPU + memory (70% target)
- **NetworkPolicies** restricting API pods to DNS, Postgres (5432), and Redis (6379) egress
- **ExternalSecret** instead of raw Kubernetes secrets
- **PodMonitor** scraping Django's `/metrics` every 15s into Prometheus

## CI/CD — GitHub Actions

- **CI** (`ci.yml`) — flake8 + pytest with Postgres/Redis services on every PR to `dev`/`main`
- **CD to EKS** (`ecr_build_deploy.yml`) — on merge to `main`:
  1. Assume the AWS deploy role via **GitHub OIDC federation** (`id-token: write`, no stored credentials)
  2. Build the prod image and push to **ECR** tagged with the short SHA
  3. **`yq`-bump** `image.tag` in `k8s/application/values-prod.yaml` and commit it back — ArgoCD detects the change and rolls out the new version (pull-based GitOps; CI never touches the cluster)
- Legacy workflows (`cd.yml`, `ecs_deploy.yml`) for the earlier GHCR + EC2/ECS deployment path are kept for reference

## Observability

- **Metrics** — kube-prometheus-stack; Django exposes `/metrics`, scraped via PodMonitor; Grafana persisted on gp3 and exposed through ingress
- **Logs** — Alloy DaemonSet ships all pod logs to Loki (7d retention, compactor enabled), queried from Grafana alongside metrics
- **Alerting-ready** — Alertmanager ships with the stack

## Application (brief)

Django 5 · DRF + SimpleJWT + drf-spectacular · PostgreSQL · Redis · Celery + Beat · S3 media (`django-storages`) · WhiteNoise static · Poetry · pytest + factory-boy

Two surfaces over the same domain: a JWT-secured JSON API and session-secured server-rendered templates. Owners manage only their own listings (`IsOwnerOrReadOnly`); unverified users' listings enter a `pending` moderation queue (Celery emails moderators).

## Local development

```bash
cp .env.example .env
./scripts/local.sh        # web + worker + beat + postgres + redis via Docker Compose
```

- App: http://localhost:8000/ · Admin: http://localhost:8000/admin/ · API docs: http://localhost:8000/api/docs/

## Deploying from scratch

```bash
# 1. Provision AWS + EKS + ArgoCD
cd renter-terraform/environments/dev
terraform init && terraform apply

# 2. Bootstrap GitOps (everything else is pulled by ArgoCD)
kubectl apply -f renter-infra/repo-secret.yaml        # repo credentials
kubectl apply -f renter-infra/argocd/root-application.yaml

# 3. Ship code — merge to main; CI builds → ECR → yq bump → ArgoCD rollout
```

## What this project demonstrates

Modular Terraform on AWS · EKS with access entries & Pod Identity · pull-based GitOps with ArgoCD app-of-apps · keyless CI/CD via GitHub OIDC · External Secrets + AWS Secrets Manager · cert-manager TLS automation · Prometheus/Grafana/Loki/Alloy observability · Helm charts with sync waves, HPA, and NetworkPolicies
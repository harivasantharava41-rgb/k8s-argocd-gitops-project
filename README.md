# Kubernetes CI/CD with Terraform & ArgoCD (GitOps Pipeline)

![Status](https://img.shields.io/badge/status-in%20progress-orange)
![Terraform](https://img.shields.io/badge/IaC-Terraform-844FBA)
![Kubernetes](https://img.shields.io/badge/Orchestration-Kubernetes-326CE5)
![ArgoCD](https://img.shields.io/badge/GitOps-ArgoCD-EF7B4D)
![Jenkins](https://img.shields.io/badge/CI-Jenkins-D24939)

**Live demo:** https://harivasantharava41-rgb.github.io/k8s-argocd-gitops-project/

A GitOps-style deployment pipeline built to solve one problem: **stop deploying by hand.**
Terraform provisions the AWS/EKS infrastructure. Jenkins builds, tests, and pushes the app
image. ArgoCD watches the repo and syncs the cluster to match it automatically — nobody,
including CI, ever runs `kubectl apply` directly against the cluster.

## Why this exists

Most CI/CD tutorials stop at "build and push a Docker image." In real production systems,
the harder problem is keeping the *running cluster* in sync with *what's in Git*, without
someone manually applying changes and accidentally causing drift. This project implements
that pattern end to end — Infrastructure as Code, containerized app, Helm packaging, and
GitOps-driven delivery — using the same tools teams run in production.

## How it flows

Developer pushes code
│
▼
Jenkins (build → test → push image → bump tag in Git)
│
▼
Git repo (single source of truth)
│
▼
ArgoCD (detects the commit, syncs automatically)
│
▼
EKS Cluster (running app, self-healing if it drifts)


## Repo structure

| Folder | Purpose |
|---|---|
| `terraform/` | AWS VPC, EKS cluster, managed node group, IAM — provisioned with remote state (S3 + DynamoDB locking) |
| `app/` | Sample Flask service + Dockerfile — the workload the pipeline ships |
| `helm-chart/` | Packaged Kubernetes manifests: Deployment, Service, HorizontalPodAutoscaler |
| `argocd/` | The GitOps contract — an Application manifest with automated sync + self-heal enabled |
| `jenkins/` | Jenkinsfile — build/test/push only; it never touches the cluster directly |

## Prerequisites

- AWS account with programmatic access (`aws configure`)
- Terraform >= 1.5
- kubectl
- Helm
- Docker + a Docker Hub account
- A GitHub repo (this one)

## Setup

**1. Bootstrap remote state** (one-time, manual)
```bash
aws s3api create-bucket --bucket <your-unique-bucket-name> --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1

aws dynamodb create-table --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region ap-south-1
```

**2. Provision infrastructure**
```bash
cd terraform
terraform init
terraform apply
aws eks update-kubeconfig --region ap-south-1 --name devops-gitops-demo
```

**3. Build and push the app image**
```bash
cd app
docker build -t <your-dockerhub-username>/gitops-demo-app:v1 .
docker push <your-dockerhub-username>/gitops-demo-app:v1
```

**4. Install ArgoCD**
```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**5. Point ArgoCD at this repo**
```bash
kubectl apply -f argocd/application.yaml
```
From here, any commit to `helm-chart/` auto-deploys — that's the GitOps part.

**6. Wire up Jenkins**
Point a Jenkins Pipeline job at `jenkins/Jenkinsfile`. On every push, it builds, pushes the
image, and bumps the tag in `helm-chart/values.yaml` — ArgoCD takes it from there.

## What this demonstrates

- **Infrastructure as Code** — a full AWS environment defined in Terraform with locked remote state
- **Container orchestration** — Deployments, Services, autoscaling, resource limits, health probes
- **GitOps** — ArgoCD as the only thing that talks to the cluster; Git is the single source of truth
- **Separation of concerns** — Jenkins builds; it never deploys directly

## Status

Actively being built out. Current focus: getting the EKS cluster and ArgoCD sync running
end to end. Follow the commit history for progress.

## Author

**Harivasanth Arava** — DevOps & Cloud Engineer
[GitHub](https://github.com/harivasantharava41-rgb) · [LinkedIn](https://linkedin.com/in/harivasanth-arava)




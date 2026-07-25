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



# k8s-argocd-gitops-project
k8s-argocd-gitops-project


# Kubernetes CI/CD with Terraform & ArgoCD (GitOps Pipeline)

A GitOps-style deployment pipeline: **Terraform** provisions the AWS/EKS infrastructure,
**Jenkins** builds and pushes the app image and updates a Git-tracked manifest, and
**ArgoCD** watches that manifest and automatically syncs the cluster to match Git —
no direct `kubectl apply` from CI.
Developer push → Jenkins (build, test, push image, bump tag in Git)
↓
Git repo (source of truth)
↓
ArgoCD (detects change, syncs cluster)
↓
EKS Cluster (running app)

## Repo structure
terraform/       AWS VPC + EKS cluster + IAM (Infrastructure as Code)
app/              Sample Flask app + Dockerfile
helm-chart/       Helm chart (Deployment, Service, HPA)
argocd/           ArgoCD Application manifest (GitOps definition)
jenkins/          Jenkinsfile (build/push/update-manifest stages)

## Prerequisites

- AWS account with programmatic access (`aws configure`)
- Terraform >= 1.5
- kubectl
- Helm
- Docker + a Docker Hub account
- A GitHub repo (push this project there first)

## 1. Bootstrap remote state (one-time, manual)

Terraform needs an S3 bucket + DynamoDB table to exist *before* `terraform init`:

```bash
aws s3api create-bucket --bucket harivasanth-devops-tfstate --region ap-south-1 \
  --create-bucket-configuration LocationConstraint=ap-south-1

aws dynamodb create-table --table-name terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region ap-south-1
```

Update the bucket name in `terraform/versions.tf` to match (must be globally unique).

## 2. Provision infrastructure with Terraform

```bash
cd terraform
terraform init
terraform plan
terraform apply
```

This creates a VPC, an EKS cluster, a managed node group, and an IAM role for Jenkins.
Takes ~15 minutes — EKS control planes are slow to provision.

Point kubectl at the new cluster:

```bash
aws eks update-kubeconfig --region ap-south-1 --name devops-gitops-demo
kubectl get nodes
```

## 3. Build and push the app image (manual first run)

```bash
cd app
docker build -t YOUR_DOCKERHUB_USERNAME/gitops-demo-app:v1 .
docker push YOUR_DOCKERHUB_USERNAME/gitops-demo-app:v1
```

Update `helm-chart/values.yaml` → `image.repository` and `image.tag` to match.

## 4. Install ArgoCD on the cluster

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# get the initial admin password
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath="{.data.password}" | base64 -d

# access the UI locally
kubectl port-forward svc/argocd-server -n argocd 8080:443
# open https://localhost:8080  (user: admin)
```

## 5. Point ArgoCD at this repo

Edit `argocd/application.yaml` → set `repoURL` to your GitHub repo, then:

```bash
kubectl apply -f argocd/application.yaml
```

ArgoCD will pull `helm-chart/`, render it, and deploy it to the `demo-app` namespace.
Because `syncPolicy.automated` is set, **any future commit to `helm-chart/` auto-deploys** —
that's the GitOps part.

Verify:

```bash
kubectl get pods -n demo-app
kubectl get svc -n demo-app
```

## 6. Wire up Jenkins

1. Install the Docker and Git plugins on Jenkins.
2. Add credentials: `dockerhub-creds` (Docker Hub) and `github-creds` (GitHub PAT).
3. Create a Pipeline job pointing at this repo, using `jenkins/Jenkinsfile`.
4. On every push, Jenkins builds the image, pushes it, and bumps `image.tag`
   in `helm-chart/values.yaml` — ArgoCD picks up that commit and redeploys automatically.

## What this project demonstrates (for interviews / resume)

- **Infrastructure as Code** — full AWS environment defined in Terraform, remote state with locking
- **Container orchestration** — Kubernetes Deployments, Services, HPA, resource limits, health probes
- **Packaging** — Helm chart instead of raw manifests
- **GitOps** — ArgoCD as the only thing that talks to the cluster; Git is the single source of truth
- **CI/CD separation of concerns** — Jenkins handles build/test/push; it never touches the cluster directly

## Notes

- `single_nat_gateway = true` and `t3.medium` nodes are cost-optimized for a personal/demo project.
  Mention in interviews that you'd use multi-AZ NAT and larger nodes for production.
- Remember to `terraform destroy` when you're done experimenting — EKS clusters cost money even when idle.

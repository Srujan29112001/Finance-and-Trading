# 🚀 CI/CD Pipeline Documentation

## Overview

This project includes a comprehensive CI/CD pipeline using **GitHub Actions** that automates:
- ✅ Testing (unit, integration, end-to-end)
- ✅ Code quality checks (linting, formatting, security)
- ✅ Docker image building and publishing
- ✅ Automated deployment to cloud (Kubernetes)
- ✅ Performance and security scanning
- ✅ Automated code reviews

---

## Table of Contents

1. [Pipeline Overview](#pipeline-overview)
2. [Workflows](#workflows)
3. [Setup Instructions](#setup-instructions)
4. [Configuration Secrets](#configuration-secrets)
5. [Running Locally](#running-locally)
6. [Deployment Process](#deployment-process)
7. [Monitoring & Alerts](#monitoring--alerts)
8. [Troubleshooting](#troubleshooting)

---

## Pipeline Overview

### Continuous Integration (CI)

Every push and pull request triggers:

```
┌─────────────────────────────────────────────────────────┐
│              Code Push / Pull Request                    │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │   GitHub Actions      │
         │   CI Pipeline         │
         └───────────┬───────────┘
                     │
    ┌────────────────┼────────────────┐
    │                │                │
┌───▼───┐      ┌────▼────┐     ┌────▼─────┐
│ Code  │      │  Unit   │     │ Docker   │
│Quality│      │ Tests   │     │  Build   │
└───┬───┘      └────┬────┘     └────┬─────┘
    │               │                │
    │  ✓ Lint       │  ✓ pytest      │  ✓ Build
    │  ✓ Format     │  ✓ Coverage    │  ✓ Scan
    │  ✓ Security   │  ✓ Integration │  ✓ Tag
    │               │                │
    └───────────────┴────────────────┘
                     │
                ┌────▼────┐
                │ All Pass│
                │   ✅    │
                └─────────┘
```

### Continuous Deployment (CD)

Successful main branch builds trigger deployment:

```
┌─────────────────────────────────────────┐
│   Main Branch Build Success             │
└──────────────┬──────────────────────────┘
               │
     ┌─────────▼─────────┐
     │ Docker Images     │
     │ Published to GHCR │
     └─────────┬─────────┘
               │
     ┌─────────▼──────────┐
     │ Deploy to Staging  │
     │ (Kubernetes)       │
     └─────────┬──────────┘
               │
     ┌─────────▼──────────┐
     │ Smoke Tests        │
     │ Performance Tests  │
     └─────────┬──────────┘
               │
          Manual Approval
               │
     ┌─────────▼──────────┐
     │ Deploy to Production│
     │ (Blue/Green)        │
     └─────────────────────┘
```

---

## Workflows

### 1. `ci.yml` - Main CI Pipeline

**Triggers:** Push to any branch, Pull Requests

**Jobs:**
1. **Code Quality** (parallel)
   - Black (formatting)
   - isort (import sorting)
   - Flake8 (linting)
   - Pylint (advanced linting)
   - Bandit (security scan)

2. **Backend Tests** (parallel)
   - pytest with coverage
   - Upload coverage to Codecov
   - PostgreSQL + Redis integration tests

3. **Docker Build** (parallel for each service)
   - Build backend, frontend, data-producers
   - Trivy security scanning
   - Cache optimization

4. **Integration Tests**
   - Docker Compose full stack test
   - API endpoint testing
   - WebSocket testing

5. **Dependency Security**
   - Safety checks for vulnerabilities
   - License compliance

6. **Documentation**
   - Markdown link checking
   - docker-compose validation

**Status:** ✅ / ❌ reported on PR

### 2. `docker-publish.yml` - Docker Image Publishing

**Triggers:** Push to main, Release tags

**Jobs:**
1. **Build & Push Multi-Arch Images**
   - linux/amd64
   - linux/arm64
   - Push to GitHub Container Registry (ghcr.io)
   - Optional: Push to Docker Hub

2. **Security Scan** published images

3. **Update Deployment Manifests**
   - Auto-update Kubernetes YAML with new image tags
   - Commit back to repo

**Published Images:**
- `ghcr.io/your-org/finance-copilot-backend:latest`
- `ghcr.io/your-org/finance-copilot-frontend:latest`
- `ghcr.io/your-org/finance-copilot-data-producers:latest`

### 3. `deploy.yml` - Automated Deployment

**Triggers:** Manual workflow_dispatch

**Inputs:**
- `environment`: staging | production
- `version`: tag to deploy (default: latest)

**Jobs:**
1. **Deploy to Kubernetes**
   - AWS EKS or GCP GKE
   - Apply manifests
   - Rolling update
   - Smoke tests

2. **Infrastructure Deployment** (Terraform)
   - Apply infrastructure changes
   - Output endpoint URLs

3. **Database Migrations**
   - Run Alembic migrations
   - Verify schema

4. **Update Monitoring**
   - Deploy Prometheus rules
   - Upload Grafana dashboards

5. **Performance Tests**
   - k6 load testing
   - Response time validation

6. **Rollback on Failure**
   - Automatic rollback if deployment fails

### 4. `code-review.yml` - Automated Code Review

**Triggers:** Pull Requests

**Jobs:**
1. **SonarCloud Analysis**
   - Code quality metrics
   - Code coverage
   - Security hotspots

2. **Complexity Analysis**
   - Cyclomatic complexity
   - Maintainability index
   - Auto-comment on PR

3. **Code Smell Detection**
   - Dead code (Vulture)
   - Anti-patterns

4. **Dependency Review**
   - Check for vulnerable dependencies
   - License compliance

5. **Security Scanning**
   - Semgrep (SAST)
   - GitGuardian (secrets)

6. **AI Code Review** (optional)
   - OpenAI-powered suggestions

---

## Setup Instructions

### Prerequisites

1. GitHub repository with Actions enabled
2. Docker Hub account (optional, for public images)
3. Cloud provider account (AWS/GCP) for deployment
4. Slack workspace (optional, for notifications)

### Step 1: Configure Repository Secrets

Go to **Settings → Secrets and Variables → Actions** and add:

#### Required Secrets

```bash
# Docker Registry
DOCKERHUB_USERNAME=your-username
DOCKERHUB_TOKEN=your-access-token

# AWS (if deploying to AWS)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key

# GCP (if deploying to GCP)
GCP_SA_KEY=your-service-account-json
GCP_PROJECT=your-project-id
GKE_CLUSTER_NAME=your-cluster-name
GKE_ZONE=us-central1-a

# Database (for migrations)
DATABASE_URL=postgresql://user:pass@host:5432/db

# Notifications (optional)
SLACK_WEBHOOK=https://hooks.slack.com/services/...

# Code Quality Tools (optional)
SONAR_TOKEN=your-sonarcloud-token
GITGUARDIAN_API_KEY=your-gitguardian-key
OPENAI_API_KEY=your-openai-key  # for AI code review

# Codecov (optional)
CODECOV_TOKEN=your-codecov-token
```

### Step 2: Configure Repository Variables

Add these as **Variables** (not secrets):

```bash
EKS_CLUSTER_NAME=finance-copilot-cluster
AWS_REGION=us-east-1
DOCKER_REGISTRY=ghcr.io
```

### Step 3: Enable GitHub Actions

1. Go to **Settings → Actions → General**
2. Set **Workflow permissions** to "Read and write permissions"
3. Check "Allow GitHub Actions to create and approve pull requests"

### Step 4: Set Up Environments

Create environments for deployment:

1. Go to **Settings → Environments**
2. Create `staging` environment
3. Create `production` environment
   - Add required reviewers
   - Add deployment branch rule: `main` only

### Step 5: Install Pre-commit Hooks (Local Development)

```bash
# Install pre-commit
pip install pre-commit

# Install the hooks
pre-commit install

# Run on all files (optional)
pre-commit run --all-files
```

---

## Configuration Secrets

### Creating Secrets

#### Docker Hub Token
```bash
# 1. Go to hub.docker.com
# 2. Account Settings → Security → New Access Token
# 3. Copy token and add to GitHub secrets
```

#### AWS Credentials
```bash
# Create IAM user with programmatic access
# Attach policies:
#   - AmazonEKSClusterPolicy
#   - AmazonEC2ContainerRegistryFullAccess
#   - AmazonS3FullAccess (for state storage)

# Add access key ID and secret to GitHub secrets
```

#### GCP Service Account
```bash
# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions"

# Grant permissions
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:github-actions@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.admin"

# Create key
gcloud iam service-accounts keys create key.json \
  --iam-account=github-actions@PROJECT_ID.iam.gserviceaccount.com

# Add key.json content to GCP_SA_KEY secret
```

---

## Running Locally

### Test CI Pipeline Locally with Act

```bash
# Install act
brew install act  # macOS
# or
curl https://raw.githubusercontent.com/nektos/act/master/install.sh | sudo bash

# Run all jobs
act

# Run specific job
act -j code-quality

# Run with secrets
act --secret-file .env.secrets
```

### Run Individual Checks

```bash
# Code formatting
black --check backend/ frontend/ data-producers/

# Linting
flake8 backend/ --max-line-length=120

# Security scan
bandit -r backend/ -ll

# Tests
cd backend && pytest tests/ -v --cov=app

# Docker build
docker build -t test-backend:local ./backend
```

---

## Deployment Process

### Manual Deployment

#### To Staging:
```bash
# Go to Actions → Deploy to Production
# Click "Run workflow"
# Select:
#   - environment: staging
#   - version: latest (or specific tag)
# Click "Run workflow"
```

#### To Production:
```bash
# Same as above but:
#   - environment: production
#   - Requires approval from designated reviewers
```

### Automatic Deployment

On every merge to `main`:
1. Docker images are built and published
2. Deployment manifests are updated
3. Staging environment is automatically deployed
4. Production requires manual trigger

### Rollback

If deployment fails:
```bash
# Automatic rollback is triggered
# Or manually:
kubectl rollout undo deployment/fastapi-backend -n finance-copilot
```

---

## Monitoring & Alerts

### Pipeline Status

View pipeline status:
- **Actions tab** in GitHub repository
- **Commits page** - see check status next to each commit
- **Pull Requests** - see checks at the bottom of PR

### Notifications

#### Slack Integration

The pipeline sends notifications to Slack for:
- ✅ Successful deployments
- ❌ Failed deployments
- 🚨 Security vulnerabilities found
- 📊 Performance regression

#### Email Notifications

GitHub sends email for:
- Workflow failures
- Required approval for production deployment

### Badges

Add to your README.md:

```markdown
![CI](https://github.com/your-org/finance-and-trading/workflows/CI/badge.svg)
![Docker Publish](https://github.com/your-org/finance-and-trading/workflows/Docker%20Publish/badge.svg)
[![codecov](https://codecov.io/gh/your-org/finance-and-trading/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/finance-and-trading)
```

---

## Troubleshooting

### Common Issues

#### 1. Docker Build Fails

**Problem:** "Error building image"

**Solution:**
```bash
# Check Dockerfile syntax
docker build -t test:local ./backend

# Check build logs in Actions tab
# Usually missing dependencies or incorrect paths
```

#### 2. Tests Fail in CI but Pass Locally

**Problem:** "Tests pass on my machine but fail in CI"

**Solutions:**
- Environment variables missing (check workflow file)
- Different Python version (align with CI)
- Database connection issues (check services in workflow)

```bash
# Run tests with same Python version as CI
pyenv install 3.11
pyenv local 3.11
pytest
```

#### 3. Deployment Timeout

**Problem:** "Deployment times out after 10 minutes"

**Solutions:**
- Increase timeout in workflow
- Check Kubernetes cluster is accessible
- Verify credentials are correct

```yaml
# In deploy.yml
timeout-minutes: 30  # Increase from 10 to 30
```

#### 4. Secrets Not Available

**Problem:** "Secret `AWS_ACCESS_KEY_ID` not found"

**Solutions:**
- Verify secret is added to repository settings
- Check secret name matches exactly (case-sensitive)
- Ensure workflow has permission to access secrets

#### 5. Image Push Fails

**Problem:** "unauthorized: authentication required"

**Solutions:**
```bash
# Verify GITHUB_TOKEN has package write permission
# Go to Settings → Actions → General
# Set Workflow permissions to "Read and write"

# For Docker Hub:
# Verify DOCKERHUB_TOKEN is valid
# Check username matches exactly
```

### Debug Mode

Enable debug logging:

1. Go to **Settings → Secrets**
2. Add secret: `ACTIONS_STEP_DEBUG` = `true`
3. Re-run workflow

### Getting Help

- **GitHub Actions Docs**: https://docs.github.com/actions
- **Docker Buildx**: https://docs.docker.com/buildx/
- **Kubernetes**: https://kubernetes.io/docs/

---

## Best Practices

### 1. Branch Protection

Set up branch protection for `main`:
- ✅ Require status checks to pass
- ✅ Require pull request reviews (2 reviewers)
- ✅ Require linear history
- ✅ Include administrators

### 2. Security

- ✅ Never commit secrets
- ✅ Use GitHub secrets for sensitive data
- ✅ Scan images before deploying
- ✅ Keep dependencies updated
- ✅ Review security alerts weekly

### 3. Testing

- ✅ Maintain >80% code coverage
- ✅ Run tests locally before pushing
- ✅ Write integration tests for critical paths
- ✅ Use test fixtures for database tests

### 4. Deployment

- ✅ Always deploy to staging first
- ✅ Run smoke tests after deployment
- ✅ Have rollback plan ready
- ✅ Monitor metrics after deployment
- ✅ Use blue/green or canary deployments for production

### 5. Performance

- ✅ Use Docker layer caching
- ✅ Run jobs in parallel where possible
- ✅ Cache Python dependencies
- ✅ Use matrix strategy for multi-service builds

---

## Metrics & KPIs

Track these metrics:

| Metric | Target | Current |
|--------|--------|---------|
| Build Time | < 10 min | - |
| Test Coverage | > 80% | - |
| Deployment Frequency | Daily | - |
| Mean Time to Recovery | < 1 hour | - |
| Change Failure Rate | < 15% | - |
| Security Issues | 0 high/critical | - |

---

## Continuous Improvement

### Regular Tasks

**Weekly:**
- Review failed builds
- Update dependencies
- Check security advisories

**Monthly:**
- Review and update workflows
- Optimize build times
- Update documentation

**Quarterly:**
- Review deployment strategy
- Evaluate new tools/actions
- Team retrospective on CI/CD

---

## Additional Resources

- [GitHub Actions Marketplace](https://github.com/marketplace?type=actions)
- [Awesome GitHub Actions](https://github.com/sdras/awesome-actions)
- [CI/CD Best Practices](https://docs.github.com/en/actions/guides)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

---

*Last Updated: November 2025*
*Pipeline Version: 1.0.0*

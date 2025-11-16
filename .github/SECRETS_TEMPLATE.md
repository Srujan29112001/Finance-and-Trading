# GitHub Secrets Configuration Template

This file lists all secrets needed for the CI/CD pipeline.
**DO NOT commit actual secret values!**

## Required Secrets

### Docker Registry

```bash
DOCKERHUB_USERNAME=          # Your Docker Hub username
DOCKERHUB_TOKEN=             # Docker Hub access token (not password!)
```

**How to create:**
1. Go to https://hub.docker.com
2. Settings → Security → New Access Token
3. Copy token (you won't see it again!)

---

### AWS Deployment (if using AWS)

```bash
AWS_ACCESS_KEY_ID=           # IAM user access key
AWS_SECRET_ACCESS_KEY=       # IAM user secret key
```

**How to create:**
```bash
# Create IAM user
aws iam create-user --user-name github-actions-finance-copilot

# Attach policies
aws iam attach-user-policy \
  --user-name github-actions-finance-copilot \
  --policy-arn arn:aws:iam::aws:policy/AmazonEKSClusterPolicy

aws iam attach-user-policy \
  --user-name github-actions-finance-copilot \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess

# Create access key
aws iam create-access-key --user-name github-actions-finance-copilot
```

---

### GCP Deployment (if using GCP)

```bash
GCP_SA_KEY=                  # Service account JSON key (entire file content)
GCP_PROJECT=                 # GCP project ID
GKE_CLUSTER_NAME=            # Kubernetes cluster name
GKE_ZONE=                    # Cluster zone (e.g., us-central1-a)
```

**How to create:**
```bash
# Set project
gcloud config set project YOUR_PROJECT_ID

# Create service account
gcloud iam service-accounts create github-actions \
  --display-name="GitHub Actions Finance Copilot"

# Grant permissions
gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.admin"

gcloud projects add-iam-policy-binding YOUR_PROJECT_ID \
  --member="serviceAccount:github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

# Create and download key
gcloud iam service-accounts keys create github-actions-key.json \
  --iam-account=github-actions@YOUR_PROJECT_ID.iam.gserviceaccount.com

# Copy content of github-actions-key.json to GCP_SA_KEY secret
cat github-actions-key.json
```

---

### Database Credentials

```bash
DATABASE_URL=                # Production database URL
# Format: postgresql://user:password@host:5432/dbname
```

---

### Notifications

```bash
SLACK_WEBHOOK=               # Slack incoming webhook URL
```

**How to create:**
1. Go to https://api.slack.com/apps
2. Create New App → From scratch
3. Incoming Webhooks → Activate
4. Add New Webhook to Workspace
5. Copy Webhook URL

---

### Code Quality Tools (Optional)

```bash
SONAR_TOKEN=                 # SonarCloud authentication token
CODECOV_TOKEN=               # Codecov upload token
GITGUARDIAN_API_KEY=         # GitGuardian API key
OPENAI_API_KEY=              # OpenAI API key for AI code review
```

#### SonarCloud Setup:
1. Go to https://sonarcloud.io
2. Add organization and project
3. Generate token: Account → Security → Generate Tokens
4. Copy token to secret

#### Codecov Setup:
1. Go to https://codecov.io
2. Link GitHub repository
3. Copy upload token from Settings
4. Add to secret

#### GitGuardian Setup:
1. Go to https://dashboard.gitguardian.com
2. API → Personal Access Tokens → Create token
3. Copy token to secret

---

## Repository Variables (Not Secrets)

These can be set as variables (not encrypted):

```bash
REGISTRY=ghcr.io                           # Container registry
IMAGE_PREFIX=your-org/finance-copilot      # Image prefix
AWS_REGION=us-east-1                       # AWS region
EKS_CLUSTER_NAME=finance-copilot-cluster   # EKS cluster name
PYTHON_VERSION=3.11                        # Python version
```

**How to add variables:**
1. Go to repository Settings
2. Secrets and variables → Actions
3. Variables tab → New repository variable

---

## How to Add Secrets to GitHub

### Via Web UI:
1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Enter name (e.g., `AWS_ACCESS_KEY_ID`)
5. Enter value
6. Click "Add secret"

### Via GitHub CLI:
```bash
# Install GitHub CLI
brew install gh  # macOS
# or download from https://cli.github.com

# Authenticate
gh auth login

# Add secret
gh secret set AWS_ACCESS_KEY_ID -b "your-access-key-id"
gh secret set AWS_SECRET_ACCESS_KEY -b "your-secret-access-key"

# Add from file
gh secret set GCP_SA_KEY < github-actions-key.json

# List secrets
gh secret list
```

---

## Environment-Specific Secrets

For staging vs production environments:

1. Go to Settings → Environments
2. Click environment name (staging/production)
3. Add environment secrets

**Example:**
- `staging` environment: `DATABASE_URL` → staging database
- `production` environment: `DATABASE_URL` → production database

---

## Security Best Practices

✅ **DO:**
- Use dedicated service accounts with minimal permissions
- Rotate secrets regularly (quarterly)
- Use environment-specific secrets
- Enable secret scanning in repository
- Use GitHub's secret scanner
- Review audit logs monthly

❌ **DON'T:**
- Commit secrets to code (check with `git secrets`)
- Share secrets in Slack/email
- Use personal credentials
- Give broad permissions
- Leave unused secrets

---

## Verify Secrets

Test secrets are working:

```bash
# Run a simple workflow that echoes (masked) secrets
# The workflow will show: ****** for actual values

gh workflow run test-secrets.yml
```

---

## Troubleshooting

### Secret not available in workflow

**Check:**
1. Secret name matches exactly (case-sensitive)
2. Workflow has permission to access secrets
3. Secret is added to correct repository
4. For environment secrets, workflow specifies environment

### Permission denied

**Solutions:**
1. Verify IAM permissions are correct
2. Check service account has required roles
3. Ensure secrets are not expired
4. Test credentials locally first

---

## Template Checklist

Use this checklist when setting up a new environment:

- [ ] Docker Hub credentials added
- [ ] Cloud provider credentials added (AWS or GCP)
- [ ] Database URL configured
- [ ] Slack webhook added (if using)
- [ ] SonarCloud token added (if using)
- [ ] Codecov token added (if using)
- [ ] All secrets tested in workflow
- [ ] Environment-specific secrets configured
- [ ] Service accounts have minimal required permissions
- [ ] Secrets documented in team password manager
- [ ] Rotation schedule planned

---

*Keep this template updated as new secrets are added!*

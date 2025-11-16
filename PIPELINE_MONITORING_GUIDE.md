# 📊 CI/CD Pipeline Monitoring Guide

Complete guide for monitoring, tracking, and optimizing your GitHub Actions CI/CD pipeline.

---

## Table of Contents

1. [Overview](#overview)
2. [Monitoring Components](#monitoring-components)
3. [Dashboards](#dashboards)
4. [Metrics Explained](#metrics-explained)
5. [Alerts and Notifications](#alerts-and-notifications)
6. [Cost Monitoring](#cost-monitoring)
7. [DORA Metrics](#dora-metrics)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

---

## Overview

The pipeline monitoring system provides comprehensive visibility into your CI/CD pipeline's health, performance, and costs. It automatically tracks metrics, generates reports, and alerts you to issues.

### What's Monitored

- ✅ **Pipeline Success Rate** - Overall reliability
- ✅ **Build Duration** - Performance trends
- ✅ **Failure Rate** - Quality indicators
- ✅ **Cost Metrics** - GitHub Actions usage and billing
- ✅ **DORA Metrics** - DevOps performance indicators
- ✅ **Workflow-specific Stats** - Detailed breakdown

### Monitoring Workflows

| Workflow | Purpose | Frequency |
|----------|---------|-----------|
| `pipeline-monitoring.yml` | Collect pipeline metrics and health checks | Every 6 hours + on workflow completion |
| `cost-monitoring.yml` | Track GitHub Actions costs and usage | Daily at 00:00 UTC |

---

## Monitoring Components

### 1. Pipeline Metrics Workflow

**File:** `.github/workflows/pipeline-monitoring.yml`

**Jobs:**
1. **collect-metrics** - Fetches last 30 days of workflow runs via GitHub API
2. **health-check** - Evaluates pipeline health against thresholds
3. **alert-on-issues** - Sends notifications when issues detected

**Outputs:**
- `.github/metrics/pipeline-metrics.json` - Raw metrics data
- `.github/metrics/pipeline-report.md` - Human-readable report

**Triggers:**
- Scheduled: Every 6 hours
- After any CI/CD workflow completes
- Manual via workflow_dispatch

### 2. Cost Monitoring Workflow

**File:** `.github/workflows/cost-monitoring.yml`

**Jobs:**
1. **track-costs** - Calculates GitHub Actions usage and costs
2. **alert-high-costs** - Notifies when costs exceed thresholds

**Outputs:**
- `.github/metrics/cost-data.json` - Cost analytics
- `.github/metrics/cost-report.md` - Cost breakdown report

**Triggers:**
- Scheduled: Daily at 00:00 UTC
- Manual via workflow_dispatch

---

## Dashboards

### 1. HTML Dashboard (Standalone)

**Location:** `.github/dashboards/pipeline-dashboard.html`

**Features:**
- Real-time metrics display
- Success rate visualization
- Workflow performance table
- Cost overview
- Automated recommendations
- Auto-refresh every 5 minutes

**Access:**
```bash
# Serve locally
cd .github/dashboards
python -m http.server 8080

# Open in browser
open http://localhost:8080/pipeline-dashboard.html
```

**Screenshot:**
```
┌─────────────────────────────────────────────┐
│ 🚀 CI/CD Pipeline Performance Dashboard    │
│ Last updated: 2025-11-16 14:30:00          │
├─────────────────────────────────────────────┤
│ Success Rate    Avg Duration    Total Runs │
│    94.9%          8.1 min          156     │
├─────────────────────────────────────────────┤
│ 📊 Workflow Performance                     │
│ ┌───────────────────────────────────────┐  │
│ │ CI/CD          89 runs   96.6%   7min│  │
│ │ Docker Publish 42 runs   95.2%  11min│  │
│ │ Deploy         25 runs   88.0%  14min│  │
│ └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

### 2. Grafana Dashboard (Advanced)

**Location:** `.github/dashboards/pipeline-performance.json`

**Panels:**
1. Success Rate (Stat with thresholds)
2. Average Duration (Time series)
3. Total Runs (Counter)
4. Failure Rate (Stat)
5. Success Rate Trend (Time series)
6. Build Duration P50/P95 (Time series)
7. Workflow Performance (Bar gauge)
8. Daily Pipeline Runs (Histogram)
9. Workflow Distribution (Pie chart)
10. Recent Failed Runs (Table)
11. Cost Metrics (Stat)
12. Deployment Frequency (DORA)
13. Lead Time for Changes (DORA)
14. Mean Time to Recovery (DORA)

**Setup:**
```bash
# 1. Install Grafana
docker run -d -p 3000:3000 --name=grafana grafana/grafana

# 2. Configure JSON data source
# In Grafana UI: Configuration → Data Sources → Add JSON

# 3. Import dashboard
# Dashboards → Import → Upload .github/dashboards/pipeline-performance.json
```

---

## Metrics Explained

### Overall Metrics

#### Success Rate
```
Success Rate = (Successful Runs / Total Runs) × 100
```

**Thresholds:**
- 🟢 ≥95%: Excellent
- 🟡 85-94%: Good
- 🟠 70-84%: Warning
- 🔴 <70%: Critical

**What it means:**
- High success rate (≥95%) = Stable, reliable pipeline
- Low success rate (<85%) = Flaky tests, infrastructure issues, or code quality problems

#### Average Duration
```
Average Duration = Sum(All Run Durations) / Total Runs
```

**Thresholds:**
- 🟢 <10 min: Excellent
- 🟡 10-15 min: Good
- 🔴 >15 min: Needs optimization

**What affects it:**
- Test suite size
- Docker build caching
- Dependency installation
- Parallel job execution

#### Failure Rate
```
Failure Rate = (Failed Runs / Total Runs) × 100
```

**Acceptable levels:**
- <5%: Excellent
- 5-10%: Good
- 10-15%: Fair
- >15%: Action required

### Per-Workflow Metrics

Each workflow tracks:
- **Total runs** - Number of executions
- **Success count** - Successful completions
- **Failure count** - Failed runs
- **Average duration** - Mean execution time
- **Success rate** - Workflow-specific reliability

### Cost Metrics

#### Total Minutes Used
Sum of all runner minutes across all workflows in the billing period.

#### Free Tier Usage
```
Free Tier Usage = (Minutes Used / 2000) × 100
```

GitHub Free tier: **2,000 minutes/month** for private repos

#### Billable Minutes
```
Billable Minutes = max(0, Total Minutes - Free Tier Minutes)
```

#### Estimated Cost
```
Linux:   $0.008/minute
Windows: $0.016/minute
macOS:   $0.08/minute
```

**Example:**
- 2,500 total minutes (all Linux)
- Free tier: 2,000 minutes
- Billable: 500 minutes
- Cost: 500 × $0.008 = **$4.00**

---

## Alerts and Notifications

### Health Check Alerts

**Triggered when:**
1. Success rate drops below 85%
2. Failure rate exceeds 15%
3. Average duration exceeds 15 minutes

**Alert channels:**
- 📧 **Slack** - Real-time notifications
- 🐛 **GitHub Issues** - Automatic issue creation
- 📬 **Email** - GitHub Actions failure emails

### Slack Alert Example

```json
{
  "text": "🚨 CI/CD Pipeline Health Alert",
  "attachments": [{
    "color": "danger",
    "fields": [
      {
        "title": "Status",
        "value": "Unhealthy"
      },
      {
        "title": "Issues",
        "value": "Success rate (82.3%) below threshold (85%)"
      },
      {
        "title": "Repository",
        "value": "your-org/finance-and-trading"
      }
    ]
  }]
}
```

### GitHub Issue Creation

When pipeline health is critical, an issue is automatically created:

**Title:** 🚨 CI/CD Pipeline Health Alert

**Labels:** `pipeline-health`, `priority-high`

**Content:**
```markdown
## Pipeline Health Issues Detected

**Status:** Unhealthy

**Issues:**
- Success rate (82.3%) below threshold (85%)
- Failure rate (17.7%) exceeds threshold (15%)

**Action Required:**
Please review the pipeline metrics and address the issues above.

[View Metrics Run](link-to-workflow-run)
```

### Cost Alerts

**Triggered when:**
1. Projected monthly cost > $10
2. Free tier usage > 90%
3. Daily usage > 200 minutes

**Example notification:**
```
💰 GitHub Actions Cost Alert

Projected monthly cost ($12.45) exceeds $10
Using 92% of free tier
High daily usage: 215 minutes/day
```

---

## Cost Monitoring

### Understanding the Cost Report

```markdown
# 💰 GitHub Actions Cost Report

**Period:** 2025-10-17 to 2025-11-16 (30 days)

## Cost Summary

| Metric | Value |
|--------|-------|
| Total Minutes Used | 2,350 min |
| Free Tier Used | 2,000 min |
| Billable Minutes | 350 min |
| **Estimated Monthly Cost** | **$2.80** |
| Avg Minutes/Day | 78.3 min |

## Cost by Workflow

| Workflow | Runs | Minutes | Est. Cost |
|----------|------|---------|-----------|
| CI Pipeline | 89 | 1,245 | $1.96 |
| Docker Publish | 42 | 756 | $0.61 |
| Deploy | 25 | 349 | $0.23 |
```

### Cost Optimization Strategies

#### 1. Optimize Docker Builds
```yaml
# Use layer caching
- name: Build Docker image
  uses: docker/build-push-action@v5
  with:
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

**Savings:** 30-50% reduction in build time

#### 2. Selective Testing
```yaml
# Only run tests on changed files
- name: Run tests
  run: |
    if git diff --name-only ${{ github.event.before }} ${{ github.sha }} | grep -E "backend/.*\.py$"; then
      pytest backend/tests
    fi
```

**Savings:** 20-40% reduction in test time

#### 3. Parallel Jobs
```yaml
jobs:
  test:
    strategy:
      matrix:
        service: [backend, frontend, data-producers]
    runs-on: ubuntu-latest
```

**Savings:** 3x faster total pipeline time

#### 4. Conditional Workflows
```yaml
on:
  push:
    branches: [main]
    paths:
      - 'backend/**'
      - '.github/workflows/backend-ci.yml'
```

**Savings:** Avoid unnecessary runs

#### 5. Self-Hosted Runners

For high-volume projects:
- **Cost:** $0/minute (after initial setup)
- **Break-even:** ~2,000+ minutes/month
- **Savings:** Up to 100%

**Setup:**
```bash
# On your server
./config.sh --url https://github.com/your-org/your-repo --token YOUR_TOKEN
./run.sh
```

---

## DORA Metrics

DORA (DevOps Research and Assessment) metrics measure DevOps team performance.

### 1. Deployment Frequency

**Definition:** How often you deploy to production

**Calculation:**
```
Deployment Frequency = Successful Deploys / Time Period
```

**Levels:**
- Elite: On-demand (multiple per day)
- High: Between once per day and once per week
- Medium: Between once per week and once per month
- Low: Less than once per month

**Track it:**
```bash
# Count successful deploy workflow runs
gh run list --workflow=deploy.yml --status=success --created="2025-11-01..2025-11-16"
```

### 2. Lead Time for Changes

**Definition:** Time from code commit to production deployment

**Calculation:**
```
Lead Time = Deploy Time - Commit Time
```

**Levels:**
- Elite: Less than one hour
- High: Less than one day
- Medium: Between one day and one week
- Low: More than one week

**Optimize:**
- Automate deployments
- Reduce build times
- Parallelize jobs
- Use feature flags

### 3. Mean Time to Recovery (MTTR)

**Definition:** Average time to recover from a production failure

**Calculation:**
```
MTTR = Sum(Recovery Times) / Number of Incidents
```

**Levels:**
- Elite: Less than one hour
- High: Less than one day
- Medium: Less than one week
- Low: More than one week

**Improve:**
- Automated rollback on failure
- Comprehensive monitoring
- Incident response playbooks
- Post-mortem reviews

### 4. Change Failure Rate

**Definition:** Percentage of deployments causing production failure

**Calculation:**
```
Change Failure Rate = (Failed Deploys / Total Deploys) × 100
```

**Levels:**
- Elite: 0-15%
- High: 16-30%
- Medium: 31-45%
- Low: >45%

**Reduce:**
- Comprehensive testing
- Staging environment validation
- Gradual rollouts
- Feature flags

---

## Troubleshooting

### Issue: Metrics Not Updating

**Symptoms:**
- Dashboard shows old data
- No new metrics files in `.github/metrics/`

**Diagnosis:**
```bash
# Check if monitoring workflow ran
gh run list --workflow=pipeline-monitoring.yml --limit=5

# View workflow logs
gh run view <run-id> --log
```

**Solutions:**
1. Verify workflow is enabled
2. Check GitHub API token permissions
3. Ensure workflows have `contents: write` permission
4. Check for workflow syntax errors

### Issue: High Failure Rate

**Symptoms:**
- Success rate below 85%
- Multiple failed runs

**Diagnosis:**
```bash
# List recent failed runs
gh run list --status=failure --limit=10

# View specific failure
gh run view <run-id> --log-failed
```

**Common causes:**
1. **Flaky tests** - Fix non-deterministic tests
2. **Infrastructure issues** - Use retry logic
3. **Dependency conflicts** - Pin versions
4. **Timeout issues** - Increase timeout limits

### Issue: Slow Build Times

**Symptoms:**
- Average duration > 15 minutes
- Builds timing out

**Diagnosis:**
```bash
# Analyze slow workflow
gh run view <run-id> --log | grep "Completed in"
```

**Solutions:**
1. **Enable caching:**
   ```yaml
   - uses: actions/cache@v4
     with:
       path: ~/.cache/pip
       key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}
   ```

2. **Parallelize jobs:**
   ```yaml
   strategy:
     matrix:
       python-version: ['3.11']
       test-group: [unit, integration, e2e]
   ```

3. **Optimize Docker builds:**
   ```yaml
   - uses: docker/build-push-action@v5
     with:
       cache-from: type=gha
       cache-to: type=gha,mode=max
   ```

### Issue: Cost Exceeding Budget

**Symptoms:**
- Projected monthly cost > $10
- Free tier exhausted

**Diagnosis:**
Check cost report at `.github/metrics/cost-report.md`

**Solutions:**
1. Reduce workflow triggers
2. Implement path filters
3. Optimize build times
4. Consider self-hosted runners

---

## Best Practices

### 1. Regular Monitoring

✅ **Do:**
- Review dashboard weekly
- Investigate failures immediately
- Track trends over time
- Set up Slack notifications

❌ **Don't:**
- Ignore warning signs
- Let failures accumulate
- Skip metric reviews

### 2. Threshold Configuration

Adjust thresholds based on your team's needs:

```yaml
# In pipeline-monitoring.yml
THRESHOLDS = {
    'min_success_rate': 85.0,      # Adjust: 80-95
    'max_avg_duration_minutes': 15.0,  # Adjust: 10-30
    'max_failure_rate': 15.0       # Adjust: 10-20
}
```

### 3. Alert Fatigue Prevention

**Good alerts:**
- Actionable
- Specific
- Context-rich
- Prioritized

**Bad alerts:**
- Too frequent
- Not actionable
- Vague
- Cry wolf

### 4. Cost Management

**Monthly review checklist:**
- [ ] Review cost report
- [ ] Identify expensive workflows
- [ ] Check for optimization opportunities
- [ ] Validate caching is working
- [ ] Review trigger conditions

### 5. Dashboard Maintenance

**Quarterly tasks:**
- [ ] Update metric thresholds
- [ ] Add new visualizations
- [ ] Remove outdated panels
- [ ] Gather team feedback
- [ ] Document changes

---

## Viewing the Monitoring Data

### Option 1: GitHub Repository

Navigate to `.github/metrics/` in your repository:
- `pipeline-metrics.json` - Raw data
- `pipeline-report.md` - Formatted report
- `cost-data.json` - Cost data
- `cost-report.md` - Cost breakdown

### Option 2: HTML Dashboard

```bash
# Clone repo
git clone https://github.com/your-org/finance-and-trading.git
cd finance-and-trading/.github/dashboards

# Serve dashboard
python -m http.server 8080

# Open browser
open http://localhost:8080/pipeline-dashboard.html
```

### Option 3: Grafana

```bash
# Start Grafana
docker run -d -p 3000:3000 grafana/grafana

# Login: admin/admin
# Import: .github/dashboards/pipeline-performance.json
```

### Option 4: Command Line

```bash
# View latest metrics
cat .github/metrics/pipeline-report.md

# View cost report
cat .github/metrics/cost-report.md

# Parse JSON with jq
jq '.success_rate' .github/metrics/pipeline-metrics.json
```

---

## Integration with Other Tools

### Slack Integration

```bash
# 1. Create Slack app
# https://api.slack.com/apps

# 2. Create incoming webhook
# Add webhook URL to repository secrets: SLACK_WEBHOOK

# 3. Test notification
curl -X POST $SLACK_WEBHOOK \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test notification from CI/CD monitoring"}'
```

### PagerDuty Integration

```yaml
- name: Alert PagerDuty
  if: failure()
  run: |
    curl -X POST https://events.pagerduty.com/v2/enqueue \
      -H 'Content-Type: application/json' \
      -d '{
        "routing_key": "${{ secrets.PAGERDUTY_KEY }}",
        "event_action": "trigger",
        "payload": {
          "summary": "Pipeline failure detected",
          "severity": "critical",
          "source": "GitHub Actions"
        }
      }'
```

### DataDog Integration

```yaml
- name: Send metrics to DataDog
  run: |
    curl -X POST "https://api.datadoghq.com/api/v1/series" \
      -H "Content-Type: application/json" \
      -H "DD-API-KEY: ${{ secrets.DATADOG_API_KEY }}" \
      -d '{
        "series": [{
          "metric": "cicd.success_rate",
          "points": [['"$(date +%s)"', 94.5]],
          "type": "gauge",
          "tags": ["environment:production"]
        }]
      }'
```

---

## FAQs

### Q: How far back does monitoring track?
**A:** 30 days of historical data by default. Adjust in workflows:
```yaml
params = {'created': f'>={(datetime.now() - timedelta(days=60)).isoformat()}'}
```

### Q: Can I monitor specific workflows only?
**A:** Yes, filter by workflow name:
```python
if workflow_name in ['CI Pipeline', 'Deploy']:
    # Track this workflow
```

### Q: How do I disable cost alerts?
**A:** Comment out the `alert-high-costs` job in `cost-monitoring.yml`

### Q: Can I export metrics to CSV?
**A:** Yes:
```python
import json
import csv

with open('.github/metrics/pipeline-metrics.json') as f:
    data = json.load(f)

with open('metrics.csv', 'w') as f:
    writer = csv.writer(f)
    writer.writerow(['Workflow', 'Runs', 'Success Rate'])
    for name, stats in data['workflows'].items():
        writer.writerow([name, stats['runs'], stats['success_rate']])
```

### Q: How accurate are cost estimates?
**A:** Estimates are based on public GitHub pricing and runner types. Actual costs may vary slightly due to:
- Runner selection (ubuntu/windows/macos)
- Concurrent job multipliers
- Storage costs
- Pricing changes

---

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/actions)
- [GitHub Actions Pricing](https://docs.github.com/billing/managing-billing-for-github-actions)
- [DORA Metrics Research](https://cloud.google.com/blog/products/devops-sre/using-the-four-keys-to-measure-your-devops-performance)
- [Grafana Documentation](https://grafana.com/docs/)
- [Slack Webhooks](https://api.slack.com/messaging/webhooks)

---

**Last Updated:** November 2025
**Version:** 1.0.0
**Maintainer:** DevOps Team

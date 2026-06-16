# DormTel CI/CD Setup

## Prerequisites

1. GitHub repository for DormTel
2. ECS instance accessible via SSH key

## Step 1: Push to GitHub

```bash
git remote add origin https://github.com/YOUR_USERNAME/dormtel-app.git
git add .
git commit -m "feat: add CI/CD pipeline for automated ECS deployment"
git push -u origin master
```

## Step 2: Configure GitHub Secrets

Go to **Settings > Secrets and variables > Actions** in your GitHub repository, then add these secrets:

| Secret | Value | How to get it |
|--------|-------|---------------|
| `ECS_HOST` | `8.220.189.33` | Your ECS public IP |
| `ECS_USER` | `ecs-user` | SSH username |
| `ECS_SSH_KEY` | Full PEM key contents | `cat evc-demo-key-pair_*.pem` |

## Step 3: Trigger Deployment

Push any commit to `master` and the pipeline will automatically:

1. Transfer updated code to `/opt/dormtel/` on ECS
2. Build and restart `api`, `frontend`, and `tenant-portal`
3. Run Alembic migrations
4. Add any missing database columns
5. Verify health checks pass
6. Confirm non-DormTel containers were not disrupted

## Monitoring

Check pipeline status in the **Actions** tab of your GitHub repository.

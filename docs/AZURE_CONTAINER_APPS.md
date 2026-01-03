# Azure Container Apps Deployment Guide

## Overview

This guide covers deploying PlanProof to **Azure Container Apps (ACA)** using Docker containers. Azure Container Apps provides a serverless container hosting solution with automatic scaling, built-in HTTPS, and pay-per-use pricing.

## Why Azure Container Apps?

✅ **Serverless** - No infrastructure management  
✅ **Auto-scaling** - Scale from 0 to N instances based on demand  
✅ **Cost-effective** - Pay only for what you use (can scale to zero)  
✅ **Simple** - Easier than Kubernetes, more flexible than App Service  
✅ **Built-in HTTPS** - Automatic TLS certificates  
✅ **Microservices ready** - Perfect for backend + frontend architecture

## Prerequisites

### Required Azure Resources

Your PlanProof project already uses these Azure services:

- ✅ **Azure PostgreSQL Flexible Server** - Database
- ✅ **Azure Blob Storage** - Document storage
- ✅ **Azure Document Intelligence** - Document extraction
- ✅ **Azure OpenAI** - LLM processing

### Required Tools

```bash
# Azure CLI (required)
az --version

# Docker Desktop (required)
docker --version

# Git (required)
git --version
```

### Install Azure CLI

**Windows:**
```powershell
winget install Microsoft.AzureCLI
```

**macOS:**
```bash
brew install azure-cli
```

**Linux:**
```bash
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
```

## Quick Start (Automated Deployment)

### Step 1: Login to Azure

```bash
az login
```

Select your Azure subscription:
```bash
az account set --subscription "Your Subscription Name"
```

### Step 2: Navigate to Project Directory

```powershell
cd "D:\Aathira Docs\PlanProof\infrastructure\azure"
```

### Step 3: Run Deployment Script

**Windows (PowerShell):**
```powershell
.\deploy-azure-aca.ps1
```

**Linux/macOS:**
```bash
chmod +x deploy-azure-aca.sh
./deploy-azure-aca.sh
```

### Step 4: Access Your Application

After deployment completes (5-10 minutes), you'll see:

```
✓ PlanProof deployed successfully to Azure Container Apps!

🌐 Application URLs:
  Frontend: https://planproof-frontend.xxx.azurecontainerapps.io
  Backend API: https://planproof-backend.xxx.azurecontainerapps.io
  API Docs: https://planproof-backend.xxx.azurecontainerapps.io/api/docs
```

## Manual Deployment (Step-by-Step)

If you prefer to understand each step:

### 1. Create Resource Group

```bash
az group create \
  --name planproof-rg \
  --location uksouth
```

### 2. Create Azure Container Registry

```bash
az acr create \
  --resource-group planproof-rg \
  --name planproofacr \
  --sku Basic \
  --admin-enabled true

az acr login --name planproofacr
```

### 3. Build and Push Docker Images

```bash
# Get ACR login server
ACR_LOGIN_SERVER=$(az acr show --name planproofacr --query loginServer -o tsv)

# Build backend
docker build \
  -f infrastructure/docker/backend.Dockerfile \
  -t ${ACR_LOGIN_SERVER}/planproof-backend:latest \
  backend/

# Build frontend
docker build \
  -f frontend/Dockerfile \
  -t ${ACR_LOGIN_SERVER}/planproof-frontend:latest \
  frontend/

# Push images
docker push ${ACR_LOGIN_SERVER}/planproof-backend:latest
docker push ${ACR_LOGIN_SERVER}/planproof-frontend:latest
```

### 4. Create Container Apps Environment

```bash
az containerapp env create \
  --name planproof-env \
  --resource-group planproof-rg \
  --location uksouth
```

### 5. Deploy Backend Container App

```bash
# Get ACR credentials
ACR_USERNAME=$(az acr credential show --name planproofacr --query username -o tsv)
ACR_PASSWORD=$(az acr credential show --name planproofacr --query passwords[0].value -o tsv)

# Deploy backend
az containerapp create \
  --name planproof-backend \
  --resource-group planproof-rg \
  --environment planproof-env \
  --image planproofacr.azurecr.io/planproof-backend:latest \
  --registry-server planproofacr.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --env-vars \
    "DATABASE_URL=${DATABASE_URL}" \
    "AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING}" \
    "AZURE_STORAGE_CONTAINER_NAME=inbox" \
    "AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}" \
    "AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}" \
    "AZURE_OPENAI_CHAT_DEPLOYMENT=gpt-4o-mini" \
    "AZURE_OPENAI_API_VERSION=2025-01-01-preview" \
    "AZURE_DOCINTEL_ENDPOINT=${AZURE_DOCINTEL_ENDPOINT}" \
    "AZURE_DOCINTEL_KEY=${AZURE_DOCINTEL_KEY}" \
    "APP_ENV=production" \
    "LOG_LEVEL=INFO" \
    "ENABLE_DB_WRITES=true" \
    "JWT_SECRET_KEY=${JWT_SECRET_KEY}"
```

### 6. Deploy Frontend Container App

```bash
# Get backend URL
BACKEND_URL=$(az containerapp show \
  --name planproof-backend \
  --resource-group planproof-rg \
  --query properties.configuration.ingress.fqdn -o tsv)

# Deploy frontend
az containerapp create \
  --name planproof-frontend \
  --resource-group planproof-rg \
  --environment planproof-env \
  --image planproofacr.azurecr.io/planproof-frontend:latest \
  --registry-server planproofacr.azurecr.io \
  --registry-username $ACR_USERNAME \
  --registry-password $ACR_PASSWORD \
  --target-port 80 \
  --ingress external \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    "VITE_API_BASE_URL=https://${BACKEND_URL}"
```

## Configuration Options

### Custom Resource Names

You can customize resource names:

**PowerShell:**
```powershell
.\deploy-azure-aca.ps1 `
  -ResourceGroup "my-rg" `
  -Location "eastus" `
  -AcrName "myacr" `
  -BackendAppName "my-backend" `
  -FrontendAppName "my-frontend"
```

**Bash:**
```bash
export RESOURCE_GROUP="my-rg"
export LOCATION="eastus"
export ACR_NAME="myacr"
export BACKEND_APP_NAME="my-backend"
export FRONTEND_APP_NAME="my-frontend"

./deploy-azure-aca.sh
```

### Scaling Configuration

Edit scaling rules:

```bash
az containerapp update \
  --name planproof-backend \
  --resource-group planproof-rg \
  --min-replicas 0 \
  --max-replicas 5
```

Scale to zero for dev environments:
```bash
az containerapp update \
  --name planproof-backend \
  --resource-group planproof-rg \
  --min-replicas 0
```

## CI/CD with GitHub Actions

### Setup

1. **Create Azure Service Principal**

```bash
az ad sp create-for-rbac \
  --name "planproof-github" \
  --role contributor \
  --scopes /subscriptions/{subscription-id}/resourceGroups/planproof-rg \
  --sdk-auth
```

Copy the JSON output.

2. **Add GitHub Secrets**

Go to: **GitHub repo → Settings → Secrets and variables → Actions**

Add these secrets:

| Secret Name | Value |
|------------|-------|
| `AZURE_CREDENTIALS` | JSON output from step 1 |
| `DATABASE_URL` | Your PostgreSQL connection string |
| `AZURE_STORAGE_CONNECTION_STRING` | Your storage account connection string |
| `AZURE_STORAGE_CONTAINER_NAME` | `inbox` |
| `AZURE_OPENAI_ENDPOINT` | Your OpenAI endpoint |
| `AZURE_OPENAI_API_KEY` | Your OpenAI API key |
| `AZURE_OPENAI_CHAT_DEPLOYMENT` | `gpt-4o-mini` |
| `AZURE_OPENAI_API_VERSION` | `2025-01-01-preview` |
| `AZURE_DOCINTEL_ENDPOINT` | Your Document Intelligence endpoint |
| `AZURE_DOCINTEL_KEY` | Your Document Intelligence key |
| `JWT_SECRET_KEY` | Your JWT secret (generate a secure one) |

3. **Push to Main Branch**

Every push to `main` will automatically deploy:

```bash
git add .
git commit -m "Deploy to Azure Container Apps"
git push origin main
```

Watch deployment progress in **Actions** tab on GitHub.

## Monitoring & Management

### View Logs

**Real-time logs:**
```bash
az containerapp logs show \
  --name planproof-backend \
  --resource-group planproof-rg \
  --follow
```

**Frontend logs:**
```bash
az containerapp logs show \
  --name planproof-frontend \
  --resource-group planproof-rg \
  --follow
```

### View Container Apps

```bash
az containerapp list \
  --resource-group planproof-rg \
  --output table
```

### Check App Status

```bash
az containerapp show \
  --name planproof-backend \
  --resource-group planproof-rg \
  --query properties.runningStatus
```

### View Metrics

```bash
# CPU usage
az monitor metrics list \
  --resource /subscriptions/{subscription-id}/resourceGroups/planproof-rg/providers/Microsoft.App/containerApps/planproof-backend \
  --metric "UsageNanoCores"

# Memory usage
az monitor metrics list \
  --resource /subscriptions/{subscription-id}/resourceGroups/planproof-rg/providers/Microsoft.App/containerApps/planproof-backend \
  --metric "WorkingSetBytes"
```

### Restart Container App

```bash
az containerapp revision restart \
  --name planproof-backend \
  --resource-group planproof-rg
```

## Updating the Application

### Update with New Code

```bash
# Pull latest code
git pull origin main

# Redeploy
cd infrastructure/azure
.\deploy-azure-aca.ps1  # Windows
./deploy-azure-aca.sh   # Linux/macOS
```

### Update Environment Variables

```bash
az containerapp update \
  --name planproof-backend \
  --resource-group planproof-rg \
  --set-env-vars \
    "LOG_LEVEL=DEBUG" \
    "ENABLE_LLM_GATE=false"
```

### Rollback to Previous Version

```bash
# List revisions
az containerapp revision list \
  --name planproof-backend \
  --resource-group planproof-rg \
  --output table

# Activate previous revision
az containerapp revision activate \
  --name planproof-backend \
  --resource-group planproof-rg \
  --revision <revision-name>
```

## Cost Optimization

### Scale to Zero (Dev/Test)

```bash
az containerapp update \
  --name planproof-backend \
  --resource-group planproof-rg \
  --min-replicas 0

az containerapp update \
  --name planproof-frontend \
  --resource-group planproof-rg \
  --min-replicas 0
```

### Estimated Costs

**Container Apps:**
- Consumption pricing: ~$0.000012/vCPU-second + $0.000002/GiB-second
- Example: Backend (1 vCPU, 2 GiB) running 8 hrs/day = ~$20/month
- Frontend (0.5 vCPU, 1 GiB) running 8 hrs/day = ~$7/month

**Container Registry (Basic):** ~$5/month

**Total Additional Cost:** ~$32/month (excluding existing Azure services)

## Troubleshooting

### Deployment Fails

```bash
# Check deployment logs
az containerapp logs show \
  --name planproof-backend \
  --resource-group planproof-rg \
  --tail 100

# Check revision status
az containerapp revision list \
  --name planproof-backend \
  --resource-group planproof-rg \
  --output table
```

### Container Won't Start

```bash
# Check container events
az containerapp revision show \
  --name planproof-backend \
  --resource-group planproof-rg \
  --revision <revision-name>

# Test image locally
docker run -it --rm \
  -p 8000:8000 \
  --env-file .env \
  planproofacr.azurecr.io/planproof-backend:latest
```

### Database Connection Issues

```bash
# Test from container
az containerapp exec \
  --name planproof-backend \
  --resource-group planproof-rg \
  --command "/bin/bash"

# Inside container:
psql $DATABASE_URL -c "SELECT 1;"
```

### CORS Errors

Update backend to allow frontend domain:

```bash
az containerapp update \
  --name planproof-backend \
  --resource-group planproof-rg \
  --set-env-vars \
    "API_CORS_ORIGINS=[\"https://planproof-frontend.xxx.azurecontainerapps.io\"]"
```

## Clean Up

### Delete Everything

```bash
az group delete \
  --name planproof-rg \
  --yes \
  --no-wait
```

### Delete Specific App

```bash
az containerapp delete \
  --name planproof-backend \
  --resource-group planproof-rg \
  --yes
```

## Next Steps

- ✅ Set up custom domain with Azure DNS
- ✅ Enable Application Insights for monitoring
- ✅ Configure Azure Key Vault for secrets
- ✅ Set up staging environment
- ✅ Enable auto-scaling based on metrics

## Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure CLI Reference](https://learn.microsoft.com/cli/azure/containerapp)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [GitHub Actions for Azure](https://github.com/Azure/actions)

## Support

For issues specific to PlanProof deployment:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [GitHub Issues](https://github.com/sgshaji/PlanProof/issues)
- Check Azure Container Apps logs

---

**Happy Deploying! 🚀**

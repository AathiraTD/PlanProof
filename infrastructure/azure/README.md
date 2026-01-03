# Azure Container Apps Deployment - Quick Reference

## Prerequisites Checklist

- [ ] Azure CLI installed (`az --version`)
- [ ] Docker Desktop running
- [ ] Logged into Azure (`az login`)
- [ ] `.env` file configured with all Azure credentials

## One-Command Deployment

**Windows:**
```powershell
cd infrastructure\azure
.\deploy-azure-aca.ps1
```

**Linux/macOS:**
```bash
cd infrastructure/azure
chmod +x deploy-azure-aca.sh
./deploy-azure-aca.sh
```

## What Gets Created

| Resource | Name | Purpose |
|----------|------|---------|
| Resource Group | `planproof-rg` | Container for all resources |
| Container Registry | `planproofacr` | Stores Docker images |
| Container App Environment | `planproof-env` | Shared environment for apps |
| Backend Container App | `planproof-backend` | FastAPI backend (port 8000) |
| Frontend Container App | `planproof-frontend` | React frontend (port 80) |

## Deployment Time

⏱️ **First deployment:** ~8-10 minutes  
⏱️ **Updates:** ~3-5 minutes

## After Deployment

You'll receive URLs like:
- Frontend: `https://planproof-frontend.xxx.azurecontainerapps.io`
- Backend API: `https://planproof-backend.xxx.azurecontainerapps.io`
- API Docs: `https://planproof-backend.xxx.azurecontainerapps.io/api/docs`

## Common Commands

**View logs:**
```bash
az containerapp logs show --name planproof-backend --resource-group planproof-rg --follow
```

**List apps:**
```bash
az containerapp list --resource-group planproof-rg -o table
```

**Update deployment:**
```bash
cd infrastructure/azure
.\deploy-azure-aca.ps1  # or ./deploy-azure-aca.sh
```

**Restart app:**
```bash
az containerapp revision restart --name planproof-backend --resource-group planproof-rg
```

## Estimated Monthly Cost

- Container Apps: $20-30/month
- Container Registry: $5/month
- **Total:** ~$25-35/month (excluding existing PostgreSQL, Storage, OpenAI)

## Need Help?

See full documentation: [AZURE_CONTAINER_APPS.md](AZURE_CONTAINER_APPS.md)

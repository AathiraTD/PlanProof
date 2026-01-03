# ==============================================================================
# PlanProof Azure Container Apps Deployment Script (PowerShell)
# ==============================================================================
# This script automates the deployment of PlanProof to Azure Container Apps
# Prerequisites: Azure CLI installed and logged in (az login)
# ==============================================================================

param(
    [string]$ResourceGroup = "planproof-rg",
    [string]$Location = "uksouth",
    [string]$AcrName = "planproofacr",
    [string]$EnvironmentName = "planproof-env",
    [string]$BackendAppName = "planproof-backend",
    [string]$FrontendAppName = "planproof-frontend",
    [string]$ImageTag = "latest"
)

$ErrorActionPreference = "Stop"

# ==============================================================================
# Helper Functions
# ==============================================================================

function Write-Header {
    param([string]$Message)
    Write-Host "`n===================================================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "===================================================================" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ $Message" -ForegroundColor Cyan
}

function Test-Prerequisites {
    Write-Header "Checking Prerequisites"
    
    # Check Azure CLI
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
        Write-Error "Azure CLI is not installed. Please install it first."
        exit 1
    }
    Write-Success "Azure CLI is installed"
    
    # Check if logged in to Azure
    try {
        az account show 2>&1 | Out-Null
        Write-Success "Logged in to Azure"
    }
    catch {
        Write-Error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    }
    
    # Check Docker
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        Write-Error "Docker is not installed. Please install Docker Desktop first."
        exit 1
    }
    Write-Success "Docker is installed"
    
    # Check .env file
    if (-not (Test-Path "..\..\.env")) {
        Write-Error ".env file not found in project root"
        exit 1
    }
    Write-Success ".env file found"
}

function New-ResourceGroupIfNotExists {
    Write-Header "Creating Resource Group"
    
    $exists = az group exists --name $ResourceGroup
    if ($exists -eq "true") {
        Write-Warning "Resource group $ResourceGroup already exists"
    }
    else {
        az group create --name $ResourceGroup --location $Location --output none
        Write-Success "Resource group $ResourceGroup created in $Location"
    }
}

function New-ContainerRegistryIfNotExists {
    Write-Header "Setting Up Azure Container Registry"
    
    try {
        az acr show --name $AcrName --resource-group $ResourceGroup 2>&1 | Out-Null
        Write-Warning "Container registry $AcrName already exists"
    }
    catch {
        Write-Info "Creating Azure Container Registry $AcrName..."
        az acr create `
            --resource-group $ResourceGroup `
            --name $AcrName `
            --sku Basic `
            --admin-enabled true `
            --output none
        Write-Success "Container registry $AcrName created"
    }
    
    # Login to ACR
    Write-Info "Logging in to Azure Container Registry..."
    az acr login --name $AcrName
    Write-Success "Logged in to ACR"
}

function Build-AndPushImages {
    Write-Header "Building and Pushing Docker Images"
    
    # Get ACR login server
    $acrLoginServer = az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer -o tsv
    Write-Info "ACR Login Server: $acrLoginServer"
    
    # Change to project root
    Push-Location ..\..\
    
    try {
        # Build backend image
        Write-Info "Building backend image..."
        docker build `
            -f infrastructure/docker/backend.Dockerfile `
            -t "${acrLoginServer}/planproof-backend:${ImageTag}" `
            backend/
        Write-Success "Backend image built"
        
        # Build frontend image
        Write-Info "Building frontend image..."
        docker build `
            -f frontend/Dockerfile `
            -t "${acrLoginServer}/planproof-frontend:${ImageTag}" `
            frontend/
        Write-Success "Frontend image built"
        
        # Push backend image
        Write-Info "Pushing backend image to ACR..."
        docker push "${acrLoginServer}/planproof-backend:${ImageTag}"
        Write-Success "Backend image pushed"
        
        # Push frontend image
        Write-Info "Pushing frontend image to ACR..."
        docker push "${acrLoginServer}/planproof-frontend:${ImageTag}"
        Write-Success "Frontend image pushed"
    }
    finally {
        Pop-Location
    }
}

function New-ContainerAppEnvironment {
    Write-Header "Creating Container Apps Environment"
    
    try {
        az containerapp env show --name $EnvironmentName --resource-group $ResourceGroup 2>&1 | Out-Null
        Write-Warning "Container Apps environment $EnvironmentName already exists"
    }
    catch {
        Write-Info "Creating Container Apps environment..."
        az containerapp env create `
            --name $EnvironmentName `
            --resource-group $ResourceGroup `
            --location $Location `
            --output none
        Write-Success "Container Apps environment $EnvironmentName created"
    }
}

function Get-EnvironmentVariables {
    Write-Header "Loading Environment Variables"
    
    # Load .env file
    $envPath = "..\..\.env"
    if (Test-Path $envPath) {
        Get-Content $envPath | ForEach-Object {
            if ($_ -match '^([^#][^=]+)=(.+)$') {
                $name = $matches[1].Trim()
                $value = $matches[2].Trim()
                Set-Variable -Name $name -Value $value -Scope Script
            }
        }
        Write-Success "Environment variables loaded from .env"
    }
    else {
        Write-Error ".env file not found"
        exit 1
    }
}

function Deploy-BackendApp {
    Write-Header "Deploying Backend Container App"
    
    $acrLoginServer = az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer -o tsv
    $acrUsername = az acr credential show --name $AcrName --query username -o tsv
    $acrPassword = az acr credential show --name $AcrName --query passwords[0].value -o tsv
    
    Write-Info "Deploying backend to Container Apps..."
    
    $envVars = @(
        "DATABASE_URL=$script:DATABASE_URL",
        "AZURE_STORAGE_CONNECTION_STRING=$script:AZURE_STORAGE_CONNECTION_STRING",
        "AZURE_STORAGE_CONTAINER_NAME=$script:AZURE_STORAGE_CONTAINER_NAME",
        "AZURE_OPENAI_ENDPOINT=$script:AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY=$script:AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_CHAT_DEPLOYMENT=$script:AZURE_OPENAI_CHAT_DEPLOYMENT",
        "AZURE_OPENAI_API_VERSION=$script:AZURE_OPENAI_API_VERSION",
        "AZURE_DOCINTEL_ENDPOINT=$script:AZURE_DOCINTEL_ENDPOINT",
        "AZURE_DOCINTEL_KEY=$script:AZURE_DOCINTEL_KEY",
        "APP_ENV=$($script:APP_ENV ?? 'production')",
        "LOG_LEVEL=$($script:LOG_LEVEL ?? 'INFO')",
        "API_VERSION=$($script:API_VERSION ?? 'v1')",
        "ENABLE_DB_WRITES=$($script:ENABLE_DB_WRITES ?? 'true')",
        "ENABLE_EXTRACTION_CACHE=$($script:ENABLE_EXTRACTION_CACHE ?? 'true')",
        "ENABLE_LLM_GATE=$($script:ENABLE_LLM_GATE ?? 'true')",
        "JWT_SECRET_KEY=$script:JWT_SECRET_KEY",
        "JWT_ALGORITHM=$($script:JWT_ALGORITHM ?? 'HS256')",
        "JWT_EXPIRATION_MINUTES=$($script:JWT_EXPIRATION_MINUTES ?? '1440')"
    )
    
    try {
        az containerapp create `
            --name $BackendAppName `
            --resource-group $ResourceGroup `
            --environment $EnvironmentName `
            --image "${acrLoginServer}/planproof-backend:${ImageTag}" `
            --registry-server $acrLoginServer `
            --registry-username $acrUsername `
            --registry-password $acrPassword `
            --target-port 8000 `
            --ingress external `
            --min-replicas 1 `
            --max-replicas 3 `
            --cpu 1.0 `
            --memory 2.0Gi `
            --env-vars $envVars `
            --output none 2>&1 | Out-Null
        Write-Success "Backend deployed successfully"
    }
    catch {
        Write-Warning "Backend app already exists, updating instead..."
        az containerapp update `
            --name $BackendAppName `
            --resource-group $ResourceGroup `
            --image "${acrLoginServer}/planproof-backend:${ImageTag}" `
            --output none
        Write-Success "Backend updated successfully"
    }
    
    $backendUrl = az containerapp show `
        --name $BackendAppName `
        --resource-group $ResourceGroup `
        --query properties.configuration.ingress.fqdn -o tsv
    
    Write-Info "Backend URL: https://$backendUrl"
}

function Deploy-FrontendApp {
    Write-Header "Deploying Frontend Container App"
    
    $acrLoginServer = az acr show --name $AcrName --resource-group $ResourceGroup --query loginServer -o tsv
    $acrUsername = az acr credential show --name $AcrName --query username -o tsv
    $acrPassword = az acr credential show --name $AcrName --query passwords[0].value -o tsv
    
    # Get backend URL
    $backendUrl = az containerapp show `
        --name $BackendAppName `
        --resource-group $ResourceGroup `
        --query properties.configuration.ingress.fqdn -o tsv
    
    Write-Info "Deploying frontend to Container Apps..."
    
    try {
        az containerapp create `
            --name $FrontendAppName `
            --resource-group $ResourceGroup `
            --environment $EnvironmentName `
            --image "${acrLoginServer}/planproof-frontend:${ImageTag}" `
            --registry-server $acrLoginServer `
            --registry-username $acrUsername `
            --registry-password $acrPassword `
            --target-port 80 `
            --ingress external `
            --min-replicas 1 `
            --max-replicas 2 `
            --cpu 0.5 `
            --memory 1.0Gi `
            --env-vars "VITE_API_BASE_URL=https://$backendUrl" `
            --output none 2>&1 | Out-Null
        Write-Success "Frontend deployed successfully"
    }
    catch {
        Write-Warning "Frontend app already exists, updating instead..."
        az containerapp update `
            --name $FrontendAppName `
            --resource-group $ResourceGroup `
            --image "${acrLoginServer}/planproof-frontend:${ImageTag}" `
            --output none
        Write-Success "Frontend updated successfully"
    }
    
    $frontendUrl = az containerapp show `
        --name $FrontendAppName `
        --resource-group $ResourceGroup `
        --query properties.configuration.ingress.fqdn -o tsv
    
    Write-Info "Frontend URL: https://$frontendUrl"
}

function Show-DeploymentSummary {
    Write-Header "Deployment Summary"
    
    $backendUrl = az containerapp show `
        --name $BackendAppName `
        --resource-group $ResourceGroup `
        --query properties.configuration.ingress.fqdn -o tsv
    
    $frontendUrl = az containerapp show `
        --name $FrontendAppName `
        --resource-group $ResourceGroup `
        --query properties.configuration.ingress.fqdn -o tsv
    
    Write-Success "PlanProof deployed successfully to Azure Container Apps!"
    Write-Host ""
    Write-Host "📋 Resource Details:" -ForegroundColor Cyan
    Write-Host "  Resource Group: $ResourceGroup"
    Write-Host "  Location: $Location"
    Write-Host "  Container Registry: $AcrName"
    Write-Host ""
    Write-Host "🌐 Application URLs:" -ForegroundColor Cyan
    Write-Host "  Frontend: https://$frontendUrl" -ForegroundColor Blue
    Write-Host "  Backend API: https://$backendUrl" -ForegroundColor Blue
    Write-Host "  API Docs: https://$backendUrl/api/docs" -ForegroundColor Blue
    Write-Host ""
    Write-Host "📊 Monitoring:" -ForegroundColor Cyan
    Write-Host "  View logs: az containerapp logs show --name $BackendAppName --resource-group $ResourceGroup --follow"
    Write-Host "  View apps: az containerapp list --resource-group $ResourceGroup -o table"
    Write-Host ""
    Write-Host "🔄 To update deployment:" -ForegroundColor Cyan
    Write-Host "  .\deploy-azure-aca.ps1"
    Write-Host ""
}

# ==============================================================================
# Main Execution
# ==============================================================================

try {
    Write-Header "PlanProof Azure Container Apps Deployment"
    
    Test-Prerequisites
    Get-EnvironmentVariables
    New-ResourceGroupIfNotExists
    New-ContainerRegistryIfNotExists
    Build-AndPushImages
    New-ContainerAppEnvironment
    Deploy-BackendApp
    Deploy-FrontendApp
    Show-DeploymentSummary
}
catch {
    Write-Error "Deployment failed: $_"
    exit 1
}

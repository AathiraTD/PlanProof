#!/bin/bash
# ==============================================================================
# PlanProof Azure Container Apps Deployment Script
# ==============================================================================
# This script automates the deployment of PlanProof to Azure Container Apps
# Prerequisites: Azure CLI installed and logged in (az login)
# ==============================================================================

set -e  # Exit on error

# ==============================================================================
# Configuration
# ==============================================================================

# Resource names
RESOURCE_GROUP="${RESOURCE_GROUP:-planproof-rg}"
LOCATION="${LOCATION:-uksouth}"
ACR_NAME="${ACR_NAME:-planproofacr}"
ENVIRONMENT_NAME="${ENVIRONMENT_NAME:-planproof-env}"
BACKEND_APP_NAME="${BACKEND_APP_NAME:-planproof-backend}"
FRONTEND_APP_NAME="${FRONTEND_APP_NAME:-planproof-frontend}"

# Container image tags
IMAGE_TAG="${IMAGE_TAG:-latest}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# ==============================================================================
# Functions
# ==============================================================================

print_header() {
    echo -e "${BLUE}===================================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}===================================================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ $1${NC}"
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check if Azure CLI is installed
    if ! command -v az &> /dev/null; then
        print_error "Azure CLI is not installed. Please install it first."
        exit 1
    fi
    print_success "Azure CLI is installed"
    
    # Check if logged in to Azure
    if ! az account show &> /dev/null; then
        print_error "Not logged in to Azure. Please run 'az login' first."
        exit 1
    fi
    print_success "Logged in to Azure"
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    print_success "Docker is installed"
    
    # Check if .env file exists
    if [ ! -f "../../.env" ]; then
        print_error ".env file not found in project root"
        exit 1
    fi
    print_success ".env file found"
    
    echo ""
}

create_resource_group() {
    print_header "Creating Resource Group"
    
    if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Resource group $RESOURCE_GROUP already exists"
    else
        az group create \
            --name "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --output none
        print_success "Resource group $RESOURCE_GROUP created in $LOCATION"
    fi
    echo ""
}

create_container_registry() {
    print_header "Setting Up Azure Container Registry"
    
    if az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Container registry $ACR_NAME already exists"
    else
        print_info "Creating Azure Container Registry $ACR_NAME..."
        az acr create \
            --resource-group "$RESOURCE_GROUP" \
            --name "$ACR_NAME" \
            --sku Basic \
            --admin-enabled true \
            --output none
        print_success "Container registry $ACR_NAME created"
    fi
    
    # Login to ACR
    print_info "Logging in to Azure Container Registry..."
    az acr login --name "$ACR_NAME"
    print_success "Logged in to ACR"
    
    echo ""
}

build_and_push_images() {
    print_header "Building and Pushing Docker Images"
    
    # Get ACR login server
    ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
    
    print_info "ACR Login Server: $ACR_LOGIN_SERVER"
    
    # Build backend image
    print_info "Building backend image..."
    cd ../../
    docker build \
        -f infrastructure/docker/backend.Dockerfile \
        -t "${ACR_LOGIN_SERVER}/planproof-backend:${IMAGE_TAG}" \
        backend/
    print_success "Backend image built"
    
    # Build frontend image
    print_info "Building frontend image..."
    docker build \
        -f frontend/Dockerfile \
        -t "${ACR_LOGIN_SERVER}/planproof-frontend:${IMAGE_TAG}" \
        frontend/
    print_success "Frontend image built"
    
    # Push backend image
    print_info "Pushing backend image to ACR..."
    docker push "${ACR_LOGIN_SERVER}/planproof-backend:${IMAGE_TAG}"
    print_success "Backend image pushed"
    
    # Push frontend image
    print_info "Pushing frontend image to ACR..."
    docker push "${ACR_LOGIN_SERVER}/planproof-frontend:${IMAGE_TAG}"
    print_success "Frontend image pushed"
    
    cd infrastructure/azure
    echo ""
}

create_container_app_environment() {
    print_header "Creating Container Apps Environment"
    
    if az containerapp env show --name "$ENVIRONMENT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
        print_warning "Container Apps environment $ENVIRONMENT_NAME already exists"
    else
        print_info "Creating Container Apps environment..."
        az containerapp env create \
            --name "$ENVIRONMENT_NAME" \
            --resource-group "$RESOURCE_GROUP" \
            --location "$LOCATION" \
            --output none
        print_success "Container Apps environment $ENVIRONMENT_NAME created"
    fi
    
    echo ""
}

load_env_vars() {
    print_header "Loading Environment Variables"
    
    # Source .env file
    if [ -f "../../.env" ]; then
        export $(cat ../../.env | grep -v '^#' | xargs)
        print_success "Environment variables loaded from .env"
    else
        print_error ".env file not found"
        exit 1
    fi
    
    echo ""
}

deploy_backend() {
    print_header "Deploying Backend Container App"
    
    ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
    ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
    ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)
    
    print_info "Deploying backend to Container Apps..."
    
    az containerapp create \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$ENVIRONMENT_NAME" \
        --image "${ACR_LOGIN_SERVER}/planproof-backend:${IMAGE_TAG}" \
        --registry-server "$ACR_LOGIN_SERVER" \
        --registry-username "$ACR_USERNAME" \
        --registry-password "$ACR_PASSWORD" \
        --target-port 8000 \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 3 \
        --cpu 1.0 \
        --memory 2.0Gi \
        --env-vars \
            "DATABASE_URL=${DATABASE_URL}" \
            "AZURE_STORAGE_CONNECTION_STRING=${AZURE_STORAGE_CONNECTION_STRING}" \
            "AZURE_STORAGE_CONTAINER_NAME=${AZURE_STORAGE_CONTAINER_NAME}" \
            "AZURE_OPENAI_ENDPOINT=${AZURE_OPENAI_ENDPOINT}" \
            "AZURE_OPENAI_API_KEY=${AZURE_OPENAI_API_KEY}" \
            "AZURE_OPENAI_CHAT_DEPLOYMENT=${AZURE_OPENAI_CHAT_DEPLOYMENT}" \
            "AZURE_OPENAI_API_VERSION=${AZURE_OPENAI_API_VERSION}" \
            "AZURE_DOCINTEL_ENDPOINT=${AZURE_DOCINTEL_ENDPOINT}" \
            "AZURE_DOCINTEL_KEY=${AZURE_DOCINTEL_KEY}" \
            "APP_ENV=${APP_ENV:-production}" \
            "LOG_LEVEL=${LOG_LEVEL:-INFO}" \
            "API_VERSION=${API_VERSION:-v1}" \
            "ENABLE_DB_WRITES=${ENABLE_DB_WRITES:-true}" \
            "ENABLE_EXTRACTION_CACHE=${ENABLE_EXTRACTION_CACHE:-true}" \
            "ENABLE_LLM_GATE=${ENABLE_LLM_GATE:-true}" \
            "JWT_SECRET_KEY=${JWT_SECRET_KEY}" \
            "JWT_ALGORITHM=${JWT_ALGORITHM:-HS256}" \
            "JWT_EXPIRATION_MINUTES=${JWT_EXPIRATION_MINUTES:-1440}" \
        --output none 2>/dev/null || {
            print_warning "Backend app already exists, updating instead..."
            az containerapp update \
                --name "$BACKEND_APP_NAME" \
                --resource-group "$RESOURCE_GROUP" \
                --image "${ACR_LOGIN_SERVER}/planproof-backend:${IMAGE_TAG}" \
                --output none
        }
    
    print_success "Backend deployed successfully"
    
    BACKEND_URL=$(az containerapp show \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn -o tsv)
    
    print_info "Backend URL: https://${BACKEND_URL}"
    
    echo ""
}

deploy_frontend() {
    print_header "Deploying Frontend Container App"
    
    ACR_LOGIN_SERVER=$(az acr show --name "$ACR_NAME" --resource-group "$RESOURCE_GROUP" --query loginServer -o tsv)
    ACR_USERNAME=$(az acr credential show --name "$ACR_NAME" --query username -o tsv)
    ACR_PASSWORD=$(az acr credential show --name "$ACR_NAME" --query passwords[0].value -o tsv)
    
    # Get backend URL for frontend to connect to
    BACKEND_URL=$(az containerapp show \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn -o tsv)
    
    print_info "Deploying frontend to Container Apps..."
    
    az containerapp create \
        --name "$FRONTEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --environment "$ENVIRONMENT_NAME" \
        --image "${ACR_LOGIN_SERVER}/planproof-frontend:${IMAGE_TAG}" \
        --registry-server "$ACR_LOGIN_SERVER" \
        --registry-username "$ACR_USERNAME" \
        --registry-password "$ACR_PASSWORD" \
        --target-port 80 \
        --ingress external \
        --min-replicas 1 \
        --max-replicas 2 \
        --cpu 0.5 \
        --memory 1.0Gi \
        --env-vars \
            "VITE_API_BASE_URL=https://${BACKEND_URL}" \
        --output none 2>/dev/null || {
            print_warning "Frontend app already exists, updating instead..."
            az containerapp update \
                --name "$FRONTEND_APP_NAME" \
                --resource-group "$RESOURCE_GROUP" \
                --image "${ACR_LOGIN_SERVER}/planproof-frontend:${IMAGE_TAG}" \
                --output none
        }
    
    print_success "Frontend deployed successfully"
    
    FRONTEND_URL=$(az containerapp show \
        --name "$FRONTEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn -o tsv)
    
    print_info "Frontend URL: https://${FRONTEND_URL}"
    
    echo ""
}

print_deployment_summary() {
    print_header "Deployment Summary"
    
    BACKEND_URL=$(az containerapp show \
        --name "$BACKEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn -o tsv)
    
    FRONTEND_URL=$(az containerapp show \
        --name "$FRONTEND_APP_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --query properties.configuration.ingress.fqdn -o tsv)
    
    echo -e "${GREEN}✓ PlanProof deployed successfully to Azure Container Apps!${NC}"
    echo ""
    echo "📋 Resource Details:"
    echo "  Resource Group: $RESOURCE_GROUP"
    echo "  Location: $LOCATION"
    echo "  Container Registry: $ACR_NAME"
    echo ""
    echo "🌐 Application URLs:"
    echo -e "  ${BLUE}Frontend:${NC} https://${FRONTEND_URL}"
    echo -e "  ${BLUE}Backend API:${NC} https://${BACKEND_URL}"
    echo -e "  ${BLUE}API Docs:${NC} https://${BACKEND_URL}/api/docs"
    echo ""
    echo "📊 Monitoring:"
    echo "  View logs: az containerapp logs show --name $BACKEND_APP_NAME --resource-group $RESOURCE_GROUP --follow"
    echo "  View apps: az containerapp list --resource-group $RESOURCE_GROUP -o table"
    echo ""
    echo "🔄 To update deployment:"
    echo "  ./deploy-azure-aca.sh"
    echo ""
}

# ==============================================================================
# Main Execution
# ==============================================================================

main() {
    print_header "PlanProof Azure Container Apps Deployment"
    echo ""
    
    check_prerequisites
    load_env_vars
    create_resource_group
    create_container_registry
    build_and_push_images
    create_container_app_environment
    deploy_backend
    deploy_frontend
    print_deployment_summary
}

# Run main function
main

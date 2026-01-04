# Docker Development Environment

This guide explains how to run PlanProof using Docker for development with proper CORS configuration.

## Quick Start

1. **Navigate to the docker directory:**
   ```bash
   cd infrastructure/docker
   ```

2. **Start the services:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```

3. **Access the application:**
   - Frontend: http://localhost:3001 (mapped from container port 3000)
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/api/docs

4. **View logs:**
   ```bash
   docker-compose -f docker-compose.dev.yml logs -f
   ```

## CORS Configuration Explained

### Frontend Configuration

The frontend uses **relative URLs** for API requests, which allows Vite's proxy to forward them to the backend:

- **`frontend/.env`**: `VITE_API_URL=` (empty/unset)
- **`vite.config.ts`**: Proxy configuration routes `/api/*` requests
  - When running in Docker: Uses `http://backend:8000` (internal Docker network)
  - When running locally: Uses `http://localhost:8000`

### Backend Configuration

The backend allows specific origins via the `API_CORS_ORIGINS` environment variable:

```yaml
API_CORS_ORIGINS: ["http://localhost:3000","http://localhost:3001","http://localhost:3002","http://localhost:8501"]
```

This ensures the backend accepts requests from the frontend running on port 3000.

### How It Works

1. Browser makes request to frontend at `http://localhost:3000`
2. Frontend code uses relative URL: `/api/v1/runs/...`
3. Vite's dev proxy intercepts and forwards to: `http://backend:8000/api/v1/runs/...`
4. Backend responds with header: `Access-Control-Allow-Origin: http://localhost:3000`
5. Browser allows the response because origins match

## Common Commands

### Start services in background
```bash
docker-compose -f docker-compose.dev.yml up -d
```

### View logs
```bash
docker-compose -f docker-compose.dev.yml logs -f
```

### Stop services
```bash
docker-compose -f docker-compose.dev.yml down
```

### Rebuild after code changes
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### Restart a single service
```bash
docker-compose -f docker-compose.dev.yml restart backend
docker-compose -f docker-compose.dev.yml restart frontend
```

## Troubleshooting CORS Issues

### Issue: "CORS policy: No 'Access-Control-Allow-Origin' header"

**Solution:**
1. Verify `VITE_API_URL` is empty in `frontend/.env`
2. Ensure backend `API_CORS_ORIGINS` includes `http://localhost:3000`
3. Restart both services after configuration changes

### Issue: "Network error" or "Failed to fetch"

**Solution:**
1. Check backend is running: `curl http://localhost:8000/api/v1/health`
2. Check frontend proxy configuration in `vite.config.ts`
3. Verify Docker network is working: `docker network ls | grep planproof`

### Issue: Changes not reflected

**Solution:**
- **Backend changes**: Auto-reloads with mounted volumes
- **Frontend changes**: Auto-reloads with Vite HMR
- **Configuration changes**: Restart services:
  ```bash
  docker-compose -f docker-compose.dev.yml restart
  ```

## Environment Variables

Key environment variables for CORS configuration:

### Frontend
- `VITE_API_URL=` - Leave empty for development with proxy
- `DOCKER_ENV=true` - Signals to use Docker network hostnames

### Backend
- `API_CORS_ORIGINS` - Array of allowed origins (JSON format)
- `APP_ENV=development` - Enables debug logging

## Volume Mounts

The docker-compose file mounts source code for hot reloading:

### Backend
- `./planproof:/app/planproof` - Python source code
- `./runs:/app/runs` - Analysis results
- `./data:/app/data` - Sample data

### Frontend
- `./frontend:/app` - React source code
- `/app/node_modules` - Isolated npm dependencies

## Health Checks

The backend includes a health check endpoint:

```bash
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "azure_services": "configured"
}
```

## Next Steps

- See [../docs/QUICKSTART.md](../../docs/QUICKSTART.md) for usage guide
- See [../docs/TROUBLESHOOTING.md](../../docs/TROUBLESHOOTING.md) for more issues
- See [../docs/DEPLOYMENT.md](../../docs/DEPLOYMENT.md) for production deployment

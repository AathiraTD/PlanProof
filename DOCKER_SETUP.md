# Docker Setup for PlanProof FastAPI Backend

This guide explains how to run the PlanProof FastAPI backend using Docker.

## Prerequisites

- Docker Desktop installed ([Download](https://docs.docker.com/get-docker/))
- Docker Compose available (included with Docker Desktop)

## Quick Start

### Option 1: Using Helper Scripts (Recommended)

**Windows (PowerShell):**
```powershell
.\start-docker-api.ps1
```

**Mac/Linux (Bash):**
```bash
chmod +x start-docker-api.sh
./start-docker-api.sh
```

### Option 2: Manual Docker Compose Commands

1. **Build the Docker image:**
```bash
docker-compose -f docker-compose.api.yml build
```

2. **Start the services:**
```bash
docker-compose -f docker-compose.api.yml up -d
```

3. **Check the logs:**
```bash
docker-compose -f docker-compose.api.yml logs -f api
```

## What Gets Started?

The Docker setup starts two services:

1. **PostgreSQL Database** (with PostGIS extension)
   - Port: 5432
   - Container: `planproof-db`

2. **FastAPI Backend**
   - Port: 8000
   - Container: `planproof-api`
   - API Docs: http://localhost:8000/api/docs
   - Health Check: http://localhost:8000/api/health

## Environment Variables

The backend uses these environment variables (configured in docker-compose.api.yml):

### Required (Auto-configured):
- `DATABASE_URL` - PostgreSQL connection string
- `JWT_SECRET_KEY` - JWT authentication secret
- `JWT_ALGORITHM` - JWT algorithm (HS256)
- `JWT_EXPIRATION_MINUTES` - Token expiration (1440 = 24 hours)

### Optional (Azure Services):
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_DOCINTEL_ENDPOINT`
- `AZURE_DOCINTEL_KEY`
- `AZURE_OPENAI_ENDPOINT`
- `AZURE_OPENAI_API_KEY`

You can override these by creating a `.env` file in the project root.

## Useful Commands

### View API Logs
```bash
docker-compose -f docker-compose.api.yml logs -f api
```

### View Database Logs
```bash
docker-compose -f docker-compose.api.yml logs -f postgres
```

### Stop All Services
```bash
docker-compose -f docker-compose.api.yml down
```

### Stop and Remove Volumes (CAUTION: Deletes database data)
```bash
docker-compose -f docker-compose.api.yml down -v
```

### Restart a Specific Service
```bash
docker-compose -f docker-compose.api.yml restart api
```

### Execute Commands in Running Container
```bash
# Access API container shell
docker exec -it planproof-api bash

# Access database
docker exec -it planproof-db psql -U planproof -d planproof
```

## Troubleshooting

### Port Already in Use

If port 8000 or 5432 is already in use:

1. **Stop the conflicting service:**
   - On Windows: Check Task Manager or `netstat -ano | findstr :8000`
   - On Mac/Linux: `lsof -i :8000` or `sudo netstat -tulpn | grep 8000`

2. **Or modify the port in docker-compose.api.yml:**
   ```yaml
   ports:
     - "8080:8000"  # Use port 8080 instead
   ```

### Container Fails to Start

1. **Check the logs:**
```bash
docker-compose -f docker-compose.api.yml logs api
```

2. **Common issues:**
   - Missing dependencies: Rebuild the image
   - Database not ready: Wait a few seconds and check again
   - Permission issues: Ensure Docker has proper permissions

### Rebuild After Code Changes

```bash
docker-compose -f docker-compose.api.yml build --no-cache
docker-compose -f docker-compose.api.yml up -d
```

## Testing the API

Once running, test with:

```bash
# Health check
curl http://localhost:8000/api/health

# API documentation
# Open in browser: http://localhost:8000/api/docs

# Test login endpoint
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "officer", "password": "demo123"}'
```

## Integration with Frontend

The frontend expects the API at `http://localhost:8000`. Once Docker is running:

1. Start your frontend (React/Vite):
   ```bash
   cd frontend
   npm run dev
   ```

2. The login page should now work!

## Production Considerations

For production deployment:

1. **Change the JWT secret:**
   - Set `JWT_SECRET_KEY` to a strong random value
   - Use environment variables or Docker secrets

2. **Use proper database credentials:**
   - Change `DB_PASSWORD` in .env file
   - Consider using a managed database service

3. **Enable HTTPS:**
   - Use a reverse proxy (nginx, traefik)
   - Configure SSL certificates

4. **Resource limits:**
   - Add resource constraints in docker-compose.yml
   - Monitor container performance

5. **Logging:**
   - Configure structured logging
   - Use a log aggregation service

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL + PostGIS Image](https://registry.hub.docker.com/r/postgis/postgis)

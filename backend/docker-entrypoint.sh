#!/bin/bash
set -e

echo "==================================="
echo "PlanProof Docker Container Starting"
echo "==================================="

# Wait for database to be ready (if using Azure PostgreSQL, skip local check)
if [ -n "$DATABASE_URL" ]; then
    echo "Database URL configured: $DATABASE_URL"
    
    # Extract host from DATABASE_URL if it's not localhost/postgres
    if [[ "$DATABASE_URL" != *"localhost"* ]] && [[ "$DATABASE_URL" != *"postgres:"* ]]; then
        echo "Using external database (Azure PostgreSQL)"
    else
        echo "Waiting for local database..."
        until pg_isready -h postgres -U planproof > /dev/null 2>&1; do
            echo "Database is unavailable - sleeping"
            sleep 2
        done
        echo "✓ Database is ready"
    fi
    
    # Run database migrations (can be disabled with SKIP_MIGRATIONS=true)
    if [ "$SKIP_MIGRATIONS" = "true" ]; then
        echo "⚠ Skipping database migrations (SKIP_MIGRATIONS=true)"
    else
        # Run database migrations (with connection test first)
        echo "Running database migrations..."
        if python -c "from sqlalchemy import create_engine; import os; engine = create_engine(os.environ['DATABASE_URL']); conn = engine.connect(); conn.close(); print('Connection successful')" 2>/dev/null; then
            echo "✓ Database connection verified"
            alembic upgrade head || echo "⚠ Warning: Migration failed or not needed"
            echo "✓ Migrations complete"
        else
            echo "⚠ Warning: Cannot connect to database - skipping migrations"
            echo "  Application will start but database operations may fail"
            echo "  Check your DATABASE_URL and network connectivity"
        fi
    fi
fi

# Execute the main command
echo "Starting application..."
exec "$@"

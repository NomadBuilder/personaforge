# Docker Setup Guide

## Do You Need Docker?

**Short answer: No, Docker is optional.**

### Without Docker (Works Fine)
- ✅ **Enrichment works** - Can analyze domains without database
- ✅ **API endpoints work** - `/api/check` doesn't need database
- ✅ **Can deploy to Render** - Render provides PostgreSQL
- ❌ **No data storage** - Results aren't saved
- ❌ **No vendor clustering** - Can't track vendors over time

### With Docker (Recommended for Local Development)
- ✅ **Local PostgreSQL** - Store enrichment results
- ✅ **Vendor tracking** - Track vendors and clusters
- ✅ **Full features** - All API endpoints work
- ✅ **Offline development** - Work without internet (after initial setup)

## Quick Start

### Option 1: Without Docker (Testing Only)
```bash
# Just test enrichment
python3 -c "
from src.enrichment.enrichment_pipeline import enrich_domain
result = enrich_domain('example.com')
print(result)
"

# Run Flask app (works without database)
python3 app.py
# Visit http://localhost:5000
# Use /api/check endpoint (doesn't need database)
```

### Option 2: With Docker (Full Features)
```bash
# Start PostgreSQL
docker-compose up -d

# Wait a few seconds for DB to start
sleep 5

# Run app
python3 app.py

# Now all features work:
# - /api/enrich (stores in database)
# - /api/vendors (shows vendor clusters)
# - /api/analytics (shows statistics)
```

## Docker Configuration

The `docker-compose.yml` sets up:
- **PostgreSQL 15** on port 5432
- **Database**: `personaforge`
- **User**: `personaforge_user`
- **Password**: `personaforge123password`

**To change credentials**, edit `docker-compose.yml` and `.env`.

## Testing

Run the test script:
```bash
./test_setup.sh
```

This will:
- ✅ Check Python and dependencies
- ✅ Test enrichment (no DB needed)
- ✅ Check Docker status
- ✅ Test database connection (if Docker running)

## Production (Render.com)

**No Docker needed!** Render provides PostgreSQL:
- Render auto-provisions PostgreSQL
- Connection details in environment variables
- No Docker required
- Just push code and deploy

## Troubleshooting

### PostgreSQL Connection Failed
```bash
# Check if container is running
docker ps | grep personaforge

# Check logs
docker-compose logs postgres

# Restart container
docker-compose restart postgres
```

### Port 5432 Already in Use
The `docker-compose.yml` is configured to use port **5433** by default to avoid conflicts with other PostgreSQL containers.

If you need to use a different port:
```bash
# 1. Change port in docker-compose.yml:
# ports:
#   - "5434:5432"  # Use 5434 instead

# 2. Set environment variable:
export POSTGRES_PORT=5434

# Or in .env file:
# POSTGRES_PORT=5434
```

### Database Not Creating Tables
The app automatically creates tables on first connection. If issues:
```bash
# Check container logs
docker-compose logs postgres

# Restart container
docker-compose restart postgres
```

## Summary

| Feature | Without Docker | With Docker |
|---------|---------------|-------------|
| Domain enrichment | ✅ Yes | ✅ Yes |
| API endpoints | ✅ Partial | ✅ Full |
| Data storage | ❌ No | ✅ Yes |
| Vendor tracking | ❌ No | ✅ Yes |
| Analytics | ❌ No | ✅ Yes |
| Deploy to Render | ✅ Yes | ✅ Yes |

**Recommendation:**
- **Testing/Development**: Docker optional
- **Local full features**: Use Docker
- **Production**: Use Render PostgreSQL (no Docker)


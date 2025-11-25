# Quick Test Guide

## Test Without Docker (Fastest)

```bash
# 1. Test enrichment (no database needed)
python3 -c "
from src.enrichment.enrichment_pipeline import enrich_domain
result = enrich_domain('example.com')
print('✅ Success!')
print(f'Domain: {result[\"domain\"]}')
print(f'IP: {result.get(\"ip_address\")}')
print(f'Registrar: {result.get(\"registrar\")}')
print(f'Host: {result.get(\"host_name\")}')
print(f'Vendor Risk: {result.get(\"vendor_risk_score\", 0)}')
"

# 2. Test Flask app (no database needed for /api/check)
python3 app.py
# Then in another terminal:
curl -X POST http://localhost:5000/api/check \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

## Test With Docker (Full Features)

```bash
# 1. Start PostgreSQL
docker-compose up -d

# 2. Wait for DB to start (5 seconds)
sleep 5

# 3. Run app
python3 app.py

# 4. Test endpoints
# Enrich and store:
curl -X POST http://localhost:5000/api/enrich \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "source": "Test"}'

# Get all domains:
curl http://localhost:5000/api/domains

# Get vendors:
curl http://localhost:5000/api/vendors

# Health check:
curl http://localhost:5000/api/health
```

## What Works Without Docker

✅ Domain enrichment (`/api/check`)
✅ Public content analysis
✅ Clearnet mirror detection
✅ Vendor detection
✅ Risk scoring
✅ All enrichment features

❌ Data storage (no database)
❌ Vendor clustering (needs stored data)
❌ Analytics (needs stored data)
❌ Graph visualization (needs Neo4j)

## What Needs Docker/PostgreSQL

✅ Storing enrichment results
✅ Vendor tracking over time
✅ Infrastructure clustering
✅ Analytics and statistics
✅ Graph relationships (Neo4j)

## Current Status

Based on tests:
- ✅ **Enrichment works** - Tested successfully
- ✅ **Flask app starts** - 18 endpoints available
- ✅ **Works without Docker** - PostgreSQL is optional
- ⚠️ **PostgreSQL available** - Can start with `docker-compose up -d`

**The app is working!** 🎉


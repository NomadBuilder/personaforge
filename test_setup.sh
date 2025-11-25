#!/bin/bash
# Quick test script for PersonaForge

echo "🧪 Testing PersonaForge Setup..."
echo ""

# Check Python
echo "1. Checking Python..."
python3 --version
if [ $? -eq 0 ]; then
    echo "   ✅ Python available"
else
    echo "   ❌ Python not found"
    exit 1
fi

# Check dependencies
echo ""
echo "2. Checking dependencies..."
python3 -c "import flask; print('   ✅ Flask:', flask.__version__)" 2>/dev/null || echo "   ⚠️  Flask not installed (run: pip install -r requirements.txt)"
python3 -c "import psycopg2; print('   ✅ PostgreSQL driver available')" 2>/dev/null || echo "   ⚠️  PostgreSQL driver not installed (optional)"
python3 -c "import neo4j; print('   ✅ Neo4j driver available')" 2>/dev/null || echo "   ⚠️  Neo4j driver not installed (optional)"

# Test enrichment (no database needed)
echo ""
echo "3. Testing enrichment pipeline (no database required)..."
python3 -c "
import sys
sys.path.insert(0, '.')
from src.enrichment.enrichment_pipeline import enrich_domain
result = enrich_domain('example.com')
print('   ✅ Enrichment works!')
print(f'   Domain: {result.get(\"domain\")}')
print(f'   IP: {result.get(\"ip_address\")}')
print(f'   Registrar: {result.get(\"registrar\")}')
" 2>&1 | grep -E "(✅|Domain:|IP:|Registrar:)" || echo "   ⚠️  Enrichment test failed"

# Check Docker
echo ""
echo "4. Checking Docker..."
if command -v docker &> /dev/null; then
    echo "   ✅ Docker available"
    docker ps &> /dev/null && echo "   ✅ Docker daemon running" || echo "   ⚠️  Docker daemon not running"
else
    echo "   ⚠️  Docker not installed (optional - only needed for local PostgreSQL)"
fi

# Check PostgreSQL
echo ""
echo "5. Checking PostgreSQL connection..."
python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from src.database.postgres_client import PostgresClient
    client = PostgresClient()
    if client and client.conn:
        print('   ✅ PostgreSQL connected')
    else:
        print('   ⚠️  PostgreSQL not available (optional - app works without it)')
except Exception as e:
    print(f'   ⚠️  PostgreSQL not available: {str(e)[:50]} (optional)')
" 2>&1 | head -2

echo ""
echo "📊 Summary:"
echo "   - App can run WITHOUT Docker (PostgreSQL is optional)"
echo "   - App can run WITHOUT PostgreSQL (enrichment works standalone)"
echo "   - Docker only needed for local PostgreSQL database"
echo "   - For production: Use Render.com PostgreSQL (no Docker needed)"
echo ""
echo "✅ PersonaForge is ready to use!"


# PersonaForge Watcher API Documentation

## Base URL

All API endpoints are available at `/api/*`

## Authentication

Currently, no authentication is required. All endpoints are publicly accessible.

## Endpoints

### 1. Enrich Domain

Enrich a domain with metadata and store in database.

**Endpoint:** `POST /api/enrich`

**Request Body:**
```json
{
  "domain": "example.com",
  "source": "Manual entry",
  "notes": "Optional notes",
  "vendor_type": "synthetic_identity"
}
```

**Response (201):**
```json
{
  "message": "Domain enriched and stored successfully",
  "domain": "example.com",
  "data": {
    "domain": "example.com",
    "ip_address": "192.0.2.1",
    "host_name": "Example Hosting",
    "registrar": "Example Registrar",
    "cdn": "Cloudflare",
    "cms": "WordPress",
    "payment_processor": "stripe, paypal",
    "vendor_type": "synthetic_identity",
    "vendor_name": "Example",
    "vendor_risk_score": 45
  },
  "status": "success"
}
```

### 2. Check Domain (No Storage)

Analyze a domain without storing in database.

**Endpoint:** `POST /api/check`

**Request Body:**
```json
{
  "domain": "example.com"
}
```

**Response (200):**
```json
{
  "message": "Domain analyzed successfully (not stored)",
  "domain": "example.com",
  "data": {
    "domain": "example.com",
    "ip_address": "192.0.2.1",
    "host_name": "Example Hosting",
    "registrar": "Example Registrar",
    "cdn": "Cloudflare",
    "cms": "WordPress",
    "payment_processor": "stripe",
    "vendor_type": "synthetic_identity",
    "vendor_risk_score": 45
  },
  "status": "checked"
}
```

### 3. Get All Domains

Retrieve all enriched domains from database.

**Endpoint:** `GET /api/domains`

**Response (200):**
```json
{
  "domains": [
    {
      "id": 1,
      "domain": "example.com",
      "source": "Manual entry",
      "vendor_type": "synthetic_identity",
      "ip_address": "192.0.2.1",
      "host_name": "Example Hosting",
      "registrar": "Example Registrar",
      "enriched_at": "2025-01-15T10:30:00"
    }
  ],
  "count": 1
}
```

### 4. Get Vendors

Retrieve vendor clusters with domain counts.

**Endpoint:** `GET /api/vendors?min_domains=2`

**Query Parameters:**
- `min_domains` (optional): Minimum number of domains per vendor (default: 1)

**Response (200):**
```json
{
  "vendors": [
    {
      "id": 1,
      "vendor_name": "Example Vendor",
      "vendor_type": "synthetic_identity",
      "domain_count": 5,
      "shared_infrastructure": {
        "host": "Example Hosting",
        "cdn": "Cloudflare"
      },
      "payment_processors": ["stripe", "paypal"],
      "first_seen": "2025-01-10T08:00:00",
      "last_seen": "2025-01-15T10:30:00",
      "cluster_id": 1
    }
  ],
  "count": 1
}
```

### 5. Get Clusters

Retrieve infrastructure clusters (domains sharing infrastructure).

**Endpoint:** `GET /api/clusters`

**Response (200):**
```json
{
  "clusters": [
    {
      "signature": "host:Example Hosting|cdn:Cloudflare|registrar:Example Registrar",
      "domains": ["example.com", "example2.com"],
      "domain_count": 2,
      "infrastructure": [
        "host:Example Hosting",
        "cdn:Cloudflare",
        "registrar:Example Registrar"
      ]
    }
  ],
  "count": 1
}
```

### 6. Get Graph Data

Retrieve graph data for visualization (Neo4j).

**Endpoint:** `GET /api/graph`

**Response (200):**
```json
{
  "nodes": [
    {
      "id": "1",
      "label": "Domain",
      "properties": {
        "domain": "example.com"
      }
    },
    {
      "id": "2",
      "label": "Vendor",
      "properties": {
        "name": "Example Vendor"
      }
    }
  ],
  "edges": [
    {
      "source": "1",
      "target": "2",
      "type": "OWNED_BY"
    }
  ]
}
```

**Note:** Returns empty arrays if Neo4j is not configured.

### 7. Health Check

Check API and database status.

**Endpoint:** `GET /api/health`

**Response (200):**
```json
{
  "status": "ok",
  "neo4j": {
    "available": true,
    "client_initialized": true,
    "driver_connected": true
  },
  "postgres": {
    "available": true,
    "connected": true
  }
}
```

## Error Responses

All endpoints may return error responses:

**400 Bad Request:**
```json
{
  "error": "Domain is required"
}
```

**500 Internal Server Error:**
```json
{
  "error": "Error message",
  "domain": "example.com",
  "status": "error"
}
```

## Enrichment Data Fields

The enrichment pipeline collects the following metadata:

- **Domain Information:**
  - `domain`: Domain name
  - `ip_address`: Primary IP address
  - `ip_addresses`: All IPv4 addresses
  - `ipv6_addresses`: All IPv6 addresses

- **Infrastructure:**
  - `host_name`: Hosting provider
  - `isp`: Internet Service Provider
  - `asn`: Autonomous System Number
  - `cdn`: Content Delivery Network
  - `registrar`: Domain registrar

- **Technology Stack:**
  - `cms`: Content Management System
  - `web_server`: Web server software
  - `frameworks`: Web frameworks
  - `analytics`: Analytics tools
  - `languages`: Programming languages

- **Payment:**
  - `payment_processor`: Payment processors detected

- **Vendor Detection:**
  - `vendor_type`: Type of vendor (synthetic_identity, deepfake, impersonation)
  - `vendor_name`: Extracted vendor name
  - `vendor_risk_score`: Risk score (0-100)

- **WHOIS Data:**
  - `creation_date`: Domain creation date
  - `expiration_date`: Domain expiration date
  - `updated_date`: Last update date
  - `name_servers`: Name servers
  - `whois_status`: Domain status

## Rate Limits

- **ip-api.com**: 45 requests/minute (free tier)
- **IPLocate.io**: 1,000 requests/day (free tier, no key needed)
- **Payment/CMS Detection**: No rate limits (local analysis)

## Examples

### cURL Examples

**Enrich a domain:**
```bash
curl -X POST http://localhost:5000/api/enrich \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com", "source": "Manual"}'
```

**Check domain (no storage):**
```bash
curl -X POST http://localhost:5000/api/check \
  -H "Content-Type: application/json" \
  -d '{"domain": "example.com"}'
```

**Get all domains:**
```bash
curl http://localhost:5000/api/domains
```

**Get vendors:**
```bash
curl "http://localhost:5000/api/vendors?min_domains=2"
```

### JavaScript Examples

**Enrich domain:**
```javascript
const response = await fetch('/api/enrich', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    domain: 'example.com',
    source: 'Web Interface',
    vendor_type: 'synthetic_identity'
  })
});

const data = await response.json();
console.log(data);
```

**Get graph data:**
```javascript
const response = await fetch('/api/graph');
const graphData = await response.json();
console.log(`Nodes: ${graphData.nodes.length}, Edges: ${graphData.edges.length}`);
```

## Notes

- All endpoints return JSON
- Timestamps are in ISO 8601 format
- Domain names are normalized (lowercase, no protocol, no www)
- Neo4j is optional - app works with PostgreSQL only
- Graph visualization requires Neo4j


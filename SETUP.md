# PersonaForge Setup Guide

## Quick Start

### 1. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start PostgreSQL (Local Development)

```bash
docker-compose up -d
```

This starts a PostgreSQL database on `localhost:5432` with:
- User: `personaforge_user`
- Password: `personaforge123password`
- Database: `personaforge`

### 3. Configure Environment

Create a `.env` file (copy from `.env.example` if available):

```bash
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=personaforge_user
POSTGRES_PASSWORD=personaforge123password
POSTGRES_DB=personaforge

FLASK_ENV=development
FLASK_DEBUG=1
SECRET_KEY=dev-secret-key-change-in-production
```

### 4. Run the Application

```bash
python app.py
```

The server will start on `http://localhost:5000`

## API Endpoints

### Enrich a Domain
```bash
POST /api/enrich
{
  "domain": "example.com",
  "source": "Manual entry",
  "notes": "Optional notes",
  "vendor_type": "synthetic_identity"
}
```

### Check Domain (No Storage)
```bash
POST /api/check
{
  "domain": "example.com"
}
```

### Get All Domains
```bash
GET /api/domains
```

### Get Vendors
```bash
GET /api/vendors?min_domains=2
```

### Get Clusters
```bash
GET /api/clusters
```

### Get Graph Data
```bash
GET /api/graph
```

### Health Check
```bash
GET /api/health
```

## Deployment to Render

1. Push code to GitHub
2. Connect repository to Render
3. Render will auto-detect `render.yaml`
4. Provision PostgreSQL database
5. Set environment variables in Render dashboard
6. Deploy!

## Project Structure

```
PersonaForge/
├── app.py                    # Flask main application
├── requirements.txt          # Python dependencies
├── render.yaml              # Render deployment config
├── docker-compose.yml       # Local PostgreSQL setup
├── Procfile                 # Production server command
├── index.html               # Landing page
├── README.md                # Project documentation
│
├── src/
│   ├── database/
│   │   ├── postgres_client.py  # PostgreSQL client
│   │   └── neo4j_client.py     # Neo4j graph client
│   │
│   ├── enrichment/
│   │   ├── enrichment_pipeline.py  # Main pipeline
│   │   ├── whois_enrichment.py    # WHOIS/DNS
│   │   ├── ip_enrichment.py       # IP geolocation
│   │   ├── cms_enrichment.py      # CMS detection
│   │   └── payment_detection.py   # Payment processors
│   │
│   ├── clustering/
│   │   └── vendor_clustering.py   # Vendor pattern detection
│   │
│   └── utils/
│       ├── config.py        # Configuration
│       ├── logger.py        # Logging
│       └── validation.py    # Input validation
│
├── templates/               # HTML templates
├── static/                  # CSS/JS assets
└── data/                    # Input/output data
```

## Features

✅ Domain enrichment (WHOIS, DNS, IP, CMS, Payment)
✅ Vendor clustering by infrastructure overlap
✅ Graph visualization (Neo4j)
✅ PostgreSQL storage
✅ Free API integrations
✅ Render deployment ready

## Next Steps

- Add vendor detection algorithms
- Build dashboard UI
- Add export functionality
- Implement AI-powered analysis (OpenAI)
- Add more enrichment sources


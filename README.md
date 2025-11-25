# PersonaForge Watcher — Synthetic Identity Intelligence Platform

**Exposing the hidden supply chain behind AI-generated identities, deepfake impersonations, and synthetic persona fraud.**

PersonaForge Watcher tracks the vendors, infrastructure, and distribution networks powering synthetic identity fraud, deepfake impersonations, and AI-constructed persona kits used in scams and extortion.

## 🎯 Mission

Identify vendors selling AI-generated identity kits, impersonation packs, deepfake personas, and fraud personas across the open web. Map their infrastructure, payment processors, hosting providers, and distribution channels to expose the supply chain enabling synthetic identity fraud.

## 🛡️ Ethical Boundaries

**What We Collect (Metadata + Public Content Analysis):**
- Domain registrations and WHOIS data
- DNS records and hosting infrastructure
- CDN providers and ASN information
- Payment processor metadata
- Public website headers and tech stack
- TLS fingerprints and Certificate Transparency
- **Public website content analysis** (keywords, patterns, descriptions)
- **Clearnet mirror detection** (much safer than dark web!)
- **Telegram channel discovery** (public channels via clearnet)
- **Public forum mentions** (Reddit, etc.)
- Threat intelligence from legitimate sources (crt.sh, URLhaus)
- **Optional dark web access** (via Tor, disabled by default)

**What We Never Do:**
- Direct dark web scraping (legal/ethical risks)
- Download or analyze harmful/illegal content
- Scrape platforms that forbid it
- Access private/restricted content
- Analyze images, videos, or files from harmful sites
- Any content involving minors or illegal material

**See [INTELLIGENCE_SOURCES.md](INTELLIGENCE_SOURCES.md) for detailed explanation of data collection strategy.**

## 🔍 What PersonaForge Tracks

### 1. Synthetic Identity Kits
Tracking sellers producing AI-generated personas used for:
- Credit fraud and identity theft
- Job impersonation scams
- Romance fraud and pig-butchering schemes
- Extortion and blackmail operations

### 2. Deepfake Impersonation Services
Monitoring kits offering:
- Video impersonation capabilities
- Voice cloning services
- Photo manipulation tools
- Used in romance scams, phishing, and blackmail

### 3. Infrastructure Mapping
Identifying:
- Domains and hosting providers
- CDNs and distribution networks
- Payment processors and wallets
- Infrastructure reused across persona shops
- AI-enabled scam networks

### 4. Vendor Pattern Detection
Clustering vendors by:
- Shared infrastructure
- Payment processor overlap
- Hosting provider concentration
- Domain registration patterns
- Distribution channel analysis

## 🏗️ Architecture

### Frontend
- Static HTML/CSS/JS (deployable on Render)
- Dark UI theme (deep gray/navy/black)
- Card-based grid layouts
- Clean sans-serif typography
- High emotional weight, forensic imagery

### Backend (Shared with ShadowStack & BlackWire)
- **Flask** web framework
- **PostgreSQL** for structured data
- **Neo4j** (optional) for graph visualization
- **Enrichment Pipeline** for metadata collection
- **Clustering** for pattern detection

### Data Sources (Free/Low-Cost APIs)
- `python-whois` - Domain registration data
- `dnspython` - DNS record lookups
- `ip-api.com` - IP geolocation (45/min free)
- `IPLocate.io` - ISP/ASN data (1,000/day free)
- `python-wappalyzer` - Tech stack detection
- `blockchain.info` - Bitcoin wallet lookups
- `blockchair.com` - Multi-crypto support

### Optional API Keys (Free Tiers)
- `BUILTWITH_API_KEY` - 10/day free (tech stack)
- `SHODAN_API_KEY` - 100/month free (infrastructure intel)
- `OPENAI_API_KEY` - AI-powered analysis and clustering

## 📊 Key Statistics

- **$20B+ annually** in synthetic identity fraud (U.S. Federal Reserve)
- **400% increase** in deepfake impersonation scams since 2022 (Europol, FTC)
- **70% of persona kits** include AI-generated faces, voices, or documents (Recorded Future)

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL (local or Render database)
- Free API keys (optional, see above)

### Setup

1. **Install dependencies:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your API keys if needed
```

3. **Start the server:**
```bash
python app.py
```

Visit `http://localhost:5000` to access PersonaForge Watcher.

## 📂 Project Structure

```
PersonaForge/
├── app.py                    # Flask web server
├── requirements.txt         # Python dependencies
├── render.yaml              # Render deployment config
├── index.html               # Landing page
├── README.md                # This file
│
├── src/
│   ├── database/
│   │   ├── neo4j_client.py  # Neo4j graph database
│   │   └── postgres_client.py # PostgreSQL client
│   │
│   ├── enrichment/
│   │   ├── domain_enrichment.py     # Domain analysis
│   │   ├── vendor_enrichment.py     # Vendor pattern detection
│   │   ├── payment_enrichment.py    # Payment processor mapping
│   │   └── enrichment_pipeline.py    # Main pipeline
│   │
│   ├── clustering/
│   │   └── vendor_clustering.py     # Vendor pattern matching
│   │
│   └── utils/
│       ├── config.py        # Configuration
│       ├── logger.py         # Logging
│       └── validation.py     # Input validation
│
├── templates/
│   ├── index.html           # Main interface
│   ├── dashboard.html       # Graph visualization
│   └── vendors.html         # Vendor listing
│
└── static/
    ├── css/
    │   └── style.css        # Styling
    └── js/
        └── visualization.js # Graph visualization
```

## 🎨 Design Language

### Visual Theme
- **Dark UI**: Deep gray (#06070d), navy, black backgrounds
- **Typography**: System fonts (Inter, system-ui, sans-serif)
- **Accents**: Red/orange gradients for CTAs (#ff6b6b, #c43434)
- **Layout**: Card-based grids with subtle borders and shadows
- **Imagery**: Forensic, sharp, no text baked into images

### Brand Consistency
PersonaForge shares visual DNA with:
- **ShadowStack** (NCII infrastructure mapping)
- **BlackWire** (fraud supply chain visualization)

All tools maintain consistent:
- Button styles and CTAs
- Card layouts
- Color schemes
- Typography hierarchy

## 🔧 API Endpoints

### Domain Enrichment
```
POST /api/enrich
Body: { "domain": "example.com" }
```

### Vendor Detection
```
GET /api/vendors
Query: ?cluster=true&min_domains=5
```

### Infrastructure Graph
```
GET /api/graph
Returns: Neo4j graph data for visualization
```

### Vendor Clustering
```
GET /api/clusters
Returns: Detected vendor clusters by infrastructure overlap
```

## 📈 Use Cases

### Financial Institutions
- Identify synthetic identity fraud patterns
- Track infrastructure behind credit scams
- Map payment processor networks

### Platform Trust & Safety
- Detect AI-generated impersonation accounts
- Identify deepfake service providers
- Monitor synthetic influencer networks

### Journalists & Researchers
- Investigate AI-enabled exploitation
- Map vendor distribution networks
- Document infrastructure enabling fraud

### NGOs & Advocacy Groups
- Monitor fraud/scam networks
- Track synthetic identity vendors
- Generate evidence for policy advocacy

## 🚢 Deployment

### Render.com (Recommended)
1. Connect GitHub repository
2. Render auto-detects `render.yaml`
3. Provision PostgreSQL database
4. Set environment variables in dashboard
5. Deploy (free tier available)

### Local Development
```bash
docker-compose up -d  # Start PostgreSQL
python app.py         # Start Flask server
```

## 📝 License & Ethics

This tool is designed for:
- **Investigative journalism**
- **Trust & safety operations**
- **Cybersecurity research**
- **NGO advocacy work**

**Not for:**
- Harassment or doxxing
- Unauthorized access
- Content analysis of harmful material

## 🤝 Contributing

This is part of the Dark AI Tools suite. See the main repository README for contribution guidelines.

## 📚 Related Tools

- **ShadowStack**: NCII infrastructure mapping
- **BlackWire**: Fraud supply chain visualization

All tools share backend infrastructure and design language.

---

**PersonaForge Watcher** — Mapping the future of synthetic identity threats


# Tor Setup Guide (Optional Dark Web Access)

## ⚠️ Legal Warning

**Before proceeding, read [LEGAL_NOTICE.md](LEGAL_NOTICE.md) and [DARK_WEB_ACCESS.md](DARK_WEB_ACCESS.md).**

Dark web access has legal risks. Consult legal counsel before use.

## Technical Setup

### 1. Install Tor

**macOS:**
```bash
brew install tor
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install tor
```

**Windows:**
Download from: https://www.torproject.org/download/

### 2. Start Tor Service

```bash
# Start Tor (runs on port 9050 by default)
tor

# Or as a service:
sudo systemctl start tor
```

### 3. Install Python Dependencies

```bash
pip install PySocks stem
```

### 4. Configure Environment

Add to `.env`:
```bash
DARKWEB_ENABLED=true
TOR_PROXY_HOST=127.0.0.1
TOR_PROXY_PORT=9050
```

### 5. Test Tor Connection

```python
import requests
import socks
import socket

socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 9050)
socket.socket = socks.socksocket

# Test with a known .onion site
response = requests.get("http://3g2upl4pq6kufc4m.onion")  # DuckDuckGo
print(response.status_code)
```

## Usage

### Enable in Code

The dark web enrichment is **disabled by default**. To enable:

1. Set `DARKWEB_ENABLED=true` in `.env`
2. Ensure Tor is running
3. The enrichment pipeline will attempt to find .onion mirrors

### Access Specific .onion Sites

```python
from src.enrichment.darkweb_enrichment import access_onion_site

# Access a .onion site
metadata = access_onion_site("example.onion")
if metadata:
    print(metadata)
```

## Content Filtering

**IMPORTANT:** The current implementation has basic filtering. You must:

1. **Implement comprehensive filtering** before production use
2. **Add ML models** for illegal content detection
3. **Add human review** of findings
4. **Never store illegal content**

## Infrastructure Requirements

### Cannot Use:
- ❌ Render.com (Tor not supported)
- ❌ AWS/Azure/GCP (Tor may violate ToS)
- ❌ Any public cloud (Tor requires special network config)

### Must Use:
- ✅ Dedicated server/VPS
- ✅ Your own infrastructure
- ✅ VPN + Tor chain (recommended)

## Recommended Setup

1. **Dedicated VPS** (DigitalOcean, Linode, etc.)
2. **Tor + VPN chain** for additional anonymity
3. **Content filtering pipeline**
4. **Audit logging**
5. **Human review process**

## Legal Compliance

Before using:

1. ✅ Consult legal counsel
2. ✅ Get written legal opinion
3. ✅ Implement content filtering
4. ✅ Document compliance procedures
5. ✅ Set up audit logging
6. ✅ Have incident response plan

## Alternative: Use Aggregated Services

**Recommended instead of direct Tor access:**
- Recorded Future API
- Flashpoint API
- Intel471 API
- ZeroFox API

These handle all legal/compliance for you.

---

**Use at your own risk. Consult legal counsel before use.**


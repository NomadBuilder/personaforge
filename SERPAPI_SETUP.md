# SerpAPI Setup

## Why SerpAPI?

The scrapers are failing because:
- **DuckDuckGo**: Returns 202 (redirect/challenge) - blocking scrapers
- **YouTube**: Playwright errors when extracting descriptions
- **Sites change**: Scrapers break when sites update their HTML structure
- **CAPTCHAs**: Sites detect and block automated scraping

**SerpAPI solves these problems:**
- ✅ Handles CAPTCHAs automatically
- ✅ Reliable JSON API (doesn't break when sites change)
- ✅ Legal compliance (API-based, not scraping)
- ✅ Structured data output
- ✅ Proxy rotation built-in

## Setup

1. **Get API Key** (Free tier: 100 searches/month)
   - Sign up at: https://serpapi.com
   - Free tier: 100 searches/month
   - Paid: $50/month for 5,000 searches

2. **Add to `.env` file:**
   ```bash
   SERPAPI_API_KEY=your_api_key_here
   ```

3. **Installation** (already done):
   ```bash
   pip install google-search-results
   ```

## Usage

The system will automatically use SerpAPI if `SERPAPI_API_KEY` is set, otherwise it falls back to scraping.

**Current status:**
- ✅ SerpAPI integration complete
- ✅ Falls back to scraping if no API key
- ⚠️  Add `SERPAPI_API_KEY` to `.env` to enable

## Cost

- **Free tier**: 100 searches/month (good for testing)
- **Paid**: $50/month for 5,000 searches
- **Enterprise**: Custom pricing for higher volumes

For PersonaForge, the free tier is enough for initial testing. If you need more, the paid tier is reasonable for the reliability it provides.


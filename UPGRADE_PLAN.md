# TrendMuse 2.0 — Upgrade Plan

## Current State Assessment

### What Works Well
- Solid FastAPI backend with modular routes (scanner, generator, converter, trends)
- SQLite database with good schema for products, price history, sessions
- Multiple site scrapers (SHEIN, ZARA, H&M, Shopify, etc.)
- GrsAI Nano Banana integration for AI design generation (Chinese prompts)
- Next.js 14 frontend with Tailwind CSS + dark mode
- Trending page with redesign functionality already working

### What's Missing
- **No real-time trend discovery** — only scrapes individual stores
- **No external trend data sources** (Google Trends, TikTok, Pinterest, Amazon)
- **No trend prediction/scoring** — just raw scraped data
- **No design workspace** — generated designs aren't saved/organized
- **Frontend feels MVP** — inline styles, inconsistent UI quality
- **No deployment config** — no Dockerfile, no Vercel config
- **API calls hardcoded to localhost:8000** in trending/trends pages

### Competitive Landscape
- **Heuritech**: AI trend forecasting for fashion brands ($$$)
- **WGSN**: Industry standard trend forecasting (enterprise)
- **Trendalytics**: Consumer-facing trend data
- **TrendMuse differentiator**: Combines trend discovery + AI design generation in one tool, accessible to small brands/indie designers

---

## Vision: TrendMuse 2.0

### Two Core Engines

#### 1. AI Trend Discovery Engine (NEW)
- Google Trends integration for fashion search volume
- Amazon Best Sellers scraping for real market signals
- Trend scoring algorithm combining multiple data sources
- Trending categories, colors, materials, styles with confidence scores

#### 2. AI Design Generation Engine (Enhanced)
- Keep existing GrsAI Nano Banana integration
- Add trend-informed design prompts
- Design workspace with save/organize/iterate
- Multi-style generation from trending items

### New Features
- **Trend Dashboard**: Real-time trending products/styles with data sources
- **Trend Discovery Page**: Multi-source trend aggregation with visual cards
- **Enhanced Design Generator**: Trend-informed, workspace-enabled
- **Professional UI**: Consistent, polished, demo-ready

---

## Implementation Priority

### Phase 1 (This Sprint)
1. ✅ Add Google Trends API endpoint
2. ✅ Add Amazon Best Sellers scraping endpoint  
3. ✅ Build Trend Discovery frontend page
4. ✅ Upgrade Dashboard to show real trend data
5. ✅ Fix all hardcoded localhost URLs (use Next.js rewrites)
6. ✅ Polish UI across all pages
7. ✅ Add deployment configs (Vercel + Railway)
8. ✅ Ensure build passes

### Phase 2 (Future)
- TikTok Creative Center integration
- Pinterest Trends integration
- Trend alerts/notifications
- Design workspace with collections
- Export to tech packs

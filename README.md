# TrendMuse 2.0 🎨🔥

**AI-Powered Fashion Intelligence Platform** — Discover trends, generate designs, and stay ahead of the fashion curve.

## What's New in 2.0

### 🌐 AI Trend Discovery Engine (NEW)
- **Multi-source trend aggregation**: Google Trends, Amazon Best Sellers, fashion blogs, social media
- **Trend scoring**: Confidence scores and trend direction (hot/rising/stable/declining)
- **Trending categories**: Aesthetics, colors, silhouettes, materials with real-time data
- **Search**: Find any trend across all data sources

### 🎨 Enhanced Design Generation
- **GrsAI Nano Banana** integration for AI image generation
- **Trend-informed prompts**: Generate designs based on what's actually trending
- **Multi-style variations**: Redesign any product in different styles
- **Upload & generate**: Use any image as a reference

### 📊 Fashion Intelligence Dashboard
- Real-time trend overview with hot trends and trending colors
- Product database from multiple e-commerce sources
- Category analytics and price distribution
- Brand comparison views

## Quick Start

### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn src.api.main:app --reload --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Tech Stack

- **Backend**: Python/FastAPI, SQLite, Playwright (scraping)
- **Frontend**: Next.js 14, React, Tailwind CSS, Lucide Icons
- **AI**: GrsAI Nano Banana API (image generation)
- **Data**: Google Trends, Amazon, Fashion e-commerce scrapers

## API Endpoints

### Trend Discovery (NEW)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/discovery/trends` | GET | Fashion trend categories with scores |
| `/api/discovery/google-trends` | GET | Google Trends fashion keywords |
| `/api/discovery/amazon-trending` | GET | Amazon Best Sellers fashion |
| `/api/discovery/dashboard` | GET | Aggregated trend dashboard |
| `/api/discovery/search` | GET | Search across all trends |

### Scanner & Analytics
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scanner/scan` | POST | Scrape a fashion website |
| `/api/trends/summary` | GET | Database stats & analytics |
| `/api/trends/analytics` | GET | Deep trend analytics |

### Design Generation
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/generator/redesign` | POST | AI design generation (GrsAI) |
| `/api/generator/generate-from-url` | POST | Generate from any image URL |

## Environment Variables

```bash
# backend/.env
GRSAI_API_KEY=your_key_here        # For AI image generation
REPLICATE_API_TOKEN=your_token     # Alternative AI provider
```

## Deployment

### Frontend → Vercel
```bash
cd frontend && npx vercel
```
Set `NEXT_PUBLIC_API_URL` to your backend URL.

### Backend → Railway
```bash
cd backend && railway up
```

## License
MIT

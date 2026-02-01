# TrendMuse 🎨

**Fashion Design AI Agent** - Analyze trends, generate designs, convert to sketches.

## Features

- 🔍 **Trend Scanner** - Scrape fashion e-commerce sites for trending styles
- ✨ **Design Generator** - Create AI-powered design variations
- ✏️ **Sketch Converter** - Transform photos into fashion sketches

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
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

- **Backend**: Python/FastAPI, Playwright, SQLite
- **Frontend**: Next.js 14, React, Tailwind CSS, shadcn/ui
- **AI**: Replicate API (prepared, uses demo mode by default)

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/scanner/scan` | POST | Scan a website for fashion items |
| `/api/scanner/items` | GET | Get scanned items |
| `/api/generator/generate` | POST | Generate design variations |
| `/api/converter/convert` | POST | Convert image to sketch |

## Environment Variables

```bash
# backend/.env
REPLICATE_API_TOKEN=your_token_here  # Optional, uses demo mode without it
```

## Demo Mode

The app runs in demo mode by default, using sample fashion data and placeholder generations. To enable real AI:

1. Get a Replicate API token
2. Set `REPLICATE_API_TOKEN` in backend/.env
3. Uncomment the API integration code in `services/image_gen.py`

## License

MIT

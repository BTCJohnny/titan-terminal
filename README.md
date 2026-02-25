# Titan Terminal

Multi-agent crypto trading intelligence powered by Claude. Get ranked signals, Wyckoff analysis, and clean trading levels every morning.

## Quick Start

### 1. Set up environment

```bash
# Copy example env and add your API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY
```

### 2. Install dependencies

**Backend (Python):**
```bash
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Initialize the database
python -c "from src.backend.db import init_db; init_db()"
```

**Frontend (Next.js):**
```bash
cd src/frontend
npm install
```

### 3. Run the system

**Terminal 1 - Backend:**
```bash
# From project root
uvicorn src.backend.api.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd src/frontend
npm run dev
```

### 4. Open the dashboard

Navigate to [http://localhost:3000](http://localhost:3000)

## Features

- **Multi-Agent Analysis**: Wyckoff specialist, Nansen on-chain, Telegram alpha, TA ensemble
- **Self-Learning**: Every signal saved to SignalJournal; mark outcomes in chat
- **Clean Levels**: Entry zone, stop loss, TP1, TP2, R:R ratio
- **Mentor Critic**: Second opinion on every signal
- **Persistent Chat**: Ask about any token or the market

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/morning-report` | GET | Get ranked trading signals |
| `/api/analyze/{symbol}` | GET | Analyze specific symbol |
| `/api/chat` | POST | Chat with the system |
| `/api/outcome` | POST | Record trade outcome |
| `/api/stats` | GET | Self-learning statistics |
| `/api/history` | GET | Signal history |

## Chat Commands

- `"analyze SOL"` - Get analysis for a specific token
- `"how's the market?"` - Market overview
- `"mark SOL as win +18%"` - Record outcome for self-learning

## Architecture

```
src/
├── backend/
│   ├── agents/           # Multi-agent system
│   │   ├── orchestrator.py  # Main brain
│   │   ├── wyckoff.py       # Wyckoff specialist
│   │   ├── nansen.py        # On-chain analysis
│   │   ├── telegram.py      # Alpha signals
│   │   ├── ta_ensemble.py   # Technical analysis
│   │   ├── risk_levels.py   # Levels & risk
│   │   └── mentor.py        # Second opinion
│   ├── api/              # FastAPI backend
│   ├── db/               # SQLite + SignalJournal
│   ├── tools/            # Data fetchers
│   └── config/           # Configuration
└── frontend/             # Next.js dashboard
```

## The 3 Laws

1. Never risk more than 2% per trade
2. Minimum 2:1 risk-reward ratio
3. Maximum 5 positions at any time

## License

MIT

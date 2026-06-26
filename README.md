# RouteMind

> Intelligent AI model routing — one interface, the right model, every time.

RouteMind eliminates the decision fatigue of choosing between AI tools. Instead of manually switching between ChatGPT, Claude, Gemini, and others depending on your task, RouteMind analyses your query and automatically routes it to the most suitable model — then explains why.

---

## 🚀 Features

### 1. Intelligent Query Routing

- **Intent Classification:** Dispatches each query to the best-fit model based on its nature (e.g. Coding → GPT-4o, Research → Gemini, Document → Claude).
- **Multi-Step Routing Pipeline:** Real-time visual feedback for intent analysis → model comparison → model selection → response generation.
- **Explainable AI Decisions:** Confidence score, estimated cost, latency, and routing reason surfaced alongside every response.
- **Adaptive Routing Policies:** Toggle between _Cost_, _Speed_, _Balanced_, and _Quality_ policies.

### 2. Rich Chat Interface

- **Auto-Resizing Text Input:** Textarea grows as you type (clamped 56px–200px), auto-focuses on load.
- **File Attachments:** Drag-and-drop or select documents, code files, and images (up to 20 MB). Validated file extensions: PDF, DOC/DOCX, TXT/MD, PNG/JPG/JPEG/WEBP, CSV, JSON, and common source-code extensions.
- **Dynamic File Icons:** Format-matched icons for attached files inside message bubbles.
- **Typing Indicator:** Step-by-step animated labels show which routing stage is active.

### 3. Premium UX & Design

- **Dark-first Theme:** Glassmorphism surfaces, glowing accents, Framer Motion transitions.
- **Theme Management:** Light / Dark / System preference via `ThemeContext`.
- **Global Notifications:** Toast system for errors, file-validation warnings, and info messages.
- **Accessible Modals:** Focus trap + Escape-key dismiss on all modal overlays.

### 4. Scalable Backend

- **FastAPI:** Clean Python backend with health monitoring and CORS.
- **Provider Adapter Pattern:** `BaseProvider` ABC — adding a new LLM = one new file.
- **Rule-Based Router:** Intent × Policy → model selection with automatic fallback.
- **Extensible Classifier:** Regex-heuristic `RuleBasedIntentClassifier` with confidence scoring.

---

## 🛠️ Tech Stack

| Layer | Choice |
| :--- | :--- |
| **Frontend Framework** | React 19 + Vite 8 |
| **Backend Framework** | FastAPI (Python 3.x) + Uvicorn |
| **Styling** | Tailwind CSS v4 |
| **Routing** | React Router v7 |
| **Animations** | Framer Motion |
| **Markdown Rendering** | `react-markdown` + `react-syntax-highlighter` + `remark-gfm` |
| **Icons** | Lucide React |
| **Unit Testing** | Vitest + React Testing Library + JSDOM |
| **CI/CD** | GitHub Actions (`ci.yml`) |
| **Deployment Routing** | Vercel SPA Rewrites (`vercel.json`) |

---

## 📂 Project Directory Structure

```
RouteMind/
├── .github/
│   └── workflows/
│       └── ci.yml               # GitHub Actions CI workflow (lint → test → build)
├── backend/                     # Python FastAPI Backend
│   ├── app/
│   │   ├── classifier/
│   │   │   └── intent_classifier.py  # BaseIntentClassifier + RuleBasedIntentClassifier
│   │   ├── config.py            # Pydantic Settings + dotenv loader
│   │   ├── main.py              # CORS, logging, router registration (lifespan)
│   │   ├── providers/
│   │   │   ├── base.py          # Abstract BaseProvider + exception hierarchy
│   │   │   ├── openai_provider.py   # Live OpenAI SDK integration
│   │   │   ├── claude_provider.py   # ⚠️ Placeholder — NotImplementedError
│   │   │   └── gemini_provider.py   # ⚠️ Placeholder — NotImplementedError
│   │   ├── routes/
│   │   │   ├── chat.py          # POST /chat — validates, classifies, routes, calls provider
│   │   │   └── health.py        # GET / and GET /health
│   │   ├── schemas/
│   │   │   └── chat.py          # ChatRequest + ChatResponse (nested: response/routing/metadata)
│   │   └── services/
│   │       ├── provider_manager.py  # Lazy-loading provider registry + health cache
│   │       └── router.py        # LLMRouter: intent × policy → RoutingDecision
│   ├── .env                     # Local environment variables (never commit secrets)
│   ├── requirements.txt         # Python dependencies
│   └── tests/                   # Pytest suite
│       ├── test_classifier.py
│       ├── test_router.py
│       ├── test_provider_manager.py
│       └── test_chat_endpoint.py
├── src/                         # React Frontend
│   ├── components/
│   │   ├── ChatInput.jsx
│   │   ├── ChatMessage.jsx
│   │   ├── RoutingCard.jsx
│   │   ├── Sidebar.jsx
│   │   ├── SettingsModal.jsx
│   │   ├── TelemetryModal.jsx
│   │   ├── TypingIndicator.jsx
│   │   ├── Tooltip.jsx
│   │   ├── Navbar.jsx
│   │   ├── Footer.jsx
│   │   └── AuthenticationComingSoonModal.jsx
│   ├── context/
│   │   ├── ThemeContext.jsx
│   │   └── ToastContext.jsx
│   ├── data/
│   │   └── mockData.js
│   ├── pages/
│   │   ├── Chat.jsx
│   │   ├── Home.jsx
│   │   ├── Benefits.jsx
│   │   └── Documentation.jsx
│   ├── services/
│   │   ├── api.js               # Fetch wrapper with AbortController timeout
│   │   └── chatService.js       # POST /chat + GET /health mappings
│   ├── utils/
│   │   ├── mockRouter.js
│   │   ├── fileHelpers.jsx
│   │   └── animations.js
│   ├── test/
│   │   ├── mockRouter.test.js
│   │   └── setup.js
│   ├── App.jsx
│   ├── main.jsx
│   └── index.css
├── index.html
├── vercel.json
├── vite.config.js
├── eslint.config.js
├── package.json
├── AGENT_CONTEXT.md
└── README.md
```

---

## ⚡ Getting Started

Requires Node.js v18+ and Python v3.9+.

### Frontend Setup

```bash
# Install dependencies
npm install        # or: pnpm install

# Start dev server (http://localhost:5173)
npm run dev        # or: pnpm dev

# Production build
npm run build      # or: pnpm build
npm run preview    # or: pnpm preview

# Lint + test
npm run lint       # ESLint check
npm run test:run   # Vitest single pass
npm run test       # Vitest watch mode
```

### Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Run tests
python -m pytest tests/ -v

# Start API server (http://127.0.0.1:8000)
uvicorn app.main:app --reload
```

Interactive API docs available at `http://127.0.0.1:8000/docs`.

### Environment Variables (`.env`)

Create `backend/.env` with:

```env
# Required for any real LLM calls
OPENAI_API_KEY=sk-...

# Required once Claude/Gemini providers are implemented
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=AIza...

# CORS — add your Vercel deployment URL here
CORS_ORIGINS=["http://localhost:5173","http://localhost:3000","https://your-app.vercel.app"]

ENVIRONMENT=development
```

---

## 📡 API Reference

### `POST /chat`

**Request:**

```json
{
  "message": "Write a fast Rust HTTP server using actix-web",
  "conversation_id": "conv_8f3a9e2d",
  "routing_policy": "quality",
  "attachments": ["server_design.pdf"],
  "user_id": "usr_9x12bc8f",
  "timestamp": "2026-06-26T07:00:00Z"
}
```

`routing_policy` must be one of: `balanced` | `speed` | `cost` | `quality`

**Response:**

```json
{
  "response": {
    "content": "Here is a minimal actix-web server...",
    "conversation_id": "conv_8f3a9e2d",
    "attachments": ["server_design.pdf"]
  },
  "routing": {
    "intent": "coding",
    "provider": "openai",
    "selected_model": "gpt-4o",
    "routing_policy": "quality",
    "confidence": 99.0,
    "reason": "Routed to GPT-4o for high-quality reasoning matching 'coding' intent under the 'quality' policy.",
    "estimated_cost": 0.00165,
    "processing_time_ms": 3250
  },
  "metadata": {
    "request_id": "req_84d72f9a1",
    "timestamp": "2026-06-26T07:00:04.123456Z",
    "status": "success",
    "api_version": "1.0.0"
  }
}
```

### `GET /health`

Returns service status and registered provider list.

---

## 🔀 Routing Logic

### Intent → Provider Mapping

| Intent | `balanced` / `cost` | `speed` | `quality` |
| :--- | :--- | :--- | :--- |
| `coding` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o` |
| `research` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o-mini` | `gemini` / `gemini-1.5-pro` |
| `document` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o-mini` | `claude` / `claude-3-5-sonnet-20241022` |
| `reasoning` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o` |
| `writing` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o-mini` | `claude` / `claude-3-5-sonnet-20241022` |
| `general` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o-mini` | `openai` / `gpt-4o` |

> ⚠️ `balanced` and `cost` currently map to identical models — no cost-weighted scoring is implemented yet.

### Fallback Chain

If the selected provider is unavailable: `openai` → `gemini` → `claude`. The first healthy provider wins.

---

## ⚠️ Known Bugs

| # | Severity | File | Description |
| :--- | :--- | :--- | :--- |
| 1 | 🔴 High | `claude_provider.py` | All methods raise `NotImplementedError` — no live Claude calls possible |
| 2 | 🔴 High | `gemini_provider.py` | All methods raise `NotImplementedError` — no live Gemini calls possible |
| 3 | 🔴 High | `requirements.txt` | Missing `anthropic`, `google-generativeai`, `pytest` packages |
| 4 | 🔴 High | `config.py` | `ANTHROPIC_API_KEY` and `GEMINI_API_KEY` not declared in `Settings` model |
| 5 | 🟡 Medium | `routes/chat.py` | Uses `list_registered_providers()` instead of `get_available_providers()` — dead providers (Claude/Gemini) treated as available at routing time |
| 6 | 🟡 Medium | `config.py` | `CORS_ORIGINS` default missing `localhost:5173` and production Vercel URL |
| 7 | 🟡 Medium | `services/api.js` | 15 s `AbortController` timeout too short for GPT-4o / Gemini Pro on long responses |
| 8 | 🟢 Low | `intent_classifier.py` | Intent tie-breaking is non-deterministic (dict key order) |
| 9 | 🟢 Low | `router.py` | `balanced` and `cost` policies resolve to identical models — no cost-weighted scoring |
| 10 | 🟢 Low | `routes/chat.py` | Flat `tokens × 0.000015` cost formula regardless of provider or model tier |
| 11 | 🟢 Low | `ChatInput.jsx` | Helper text uses `text-[11px]` — below the 12 px accessibility floor |
| 12 | 🟢 Low | `Tooltip.jsx` | Hover-only; not keyboard or screen-reader accessible |
| 13 | 🟢 Low | `Chat.jsx` | `handleNewChat` in header is an inline lambda instead of calling the shared handler |
| 14 | 🟢 Low | `chatService.js` | No SSE streaming — full response is buffered before rendering |

---

## ⚙️ CI/CD Pipeline

Every push and pull request to `main` triggers the GitHub Actions workflow (`ci.yml`):

1. **Lint** — ESLint with React rules
2. **Test** — Vitest unit tests (`pnpm test:run`)
3. **Build** — Vite production build

---

## 🌐 Deployment

- **Frontend:** Vercel. `vercel.json` rewrites all routes to `index.html` (standard SPA pattern). Push to `main` auto-deploys.
- **Backend:** Not yet deployed. Planned target: Railway (FastAPI + Uvicorn).

---

## 👥 Team

- [pritesh-4](https://github.com/pritesh-4)
- [adarsh-67r](https://github.com/adarsh-67r)

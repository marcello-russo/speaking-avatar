# Speaking Avatar

Open source 3D speaking avatar microservice. Drop-in web component for AI-powered tutoring, customer support, or any conversational UI.

```html
<script src="https://cdn.example.com/speaking-avatar.js"></script>
<speaking-avatar context="Mathematics" accent="#6366f1"></speaking-avatar>
```

## Features

- **3D avatar** with lip-sync, expressions, and gestures (Three.js)
- **Text-to-speech** in 100+ languages (Edge TTS)
- **AI-powered chat** via OpenRouter or any OpenAI-compatible API
- **Web Component** — works in any framework or plain HTML
- **Customizable** — accent color, theme, avatar model, system prompt
- **Docker** — one command to run the full stack

## Quick Start

```bash
git clone https://github.com/marcello-russo/speaking-avatar
cd speaking-avatar

# 1. Configure API key
cp backend/.env.example backend/.env
# Edit backend/.env and add your OPENROUTER_API_KEY

# 2. Start everything
docker compose up -d
```

Open http://localhost:5173

## Usage

### As Web Component

```html
<script type="module" src="http://localhost:5173/src/main.js"></script>
<speaking-avatar
  context="Mathematics"
  theme="light"
  accent="#6366f1"
  apiurl="http://localhost:8000/api/v1"
></speaking-avatar>
```

### Props

| Prop | Default | Description |
|------|---------|-------------|
| `context` | `""` | Context passed to the AI (e.g. course name) |
| `theme` | `"light"` | `"light"` or `"dark"` |
| `accent` | `"#6366f1"` | Accent color for UI elements |
| `apiurl` | `"http://localhost:8000/api/v1"` | Backend API base URL |
| `avatar` | `"The Scholar"` | 3D avatar model to use |
| `title` | `"AI Tutor"` | Title shown in chat header |
| `fab` | `"true"` | Show/hide floating action button |

### API

| Route | Description |
|-------|-------------|
| `GET /api/v1/health` | Health check |
| `POST /api/v1/chat` | Send message, get AI response |
| `POST /api/v1/tts` | Text-to-speech (returns audio) |

## Architecture

```
┌──────────────────────────────────────────┐
│          <speaking-avatar>               │
│  Web Component (Svelte → Custom Element) │
│  ├── Three.js 3D renderer               │
│  ├── Edge TTS (browser audio)           │
│  └── Chat UI                            │
└────────────────┬─────────────────────────┘
                 │ REST API
┌────────────────▼─────────────────────────┐
│          Backend (FastAPI)                │
│  /api/v1/chat  /api/v1/tts  /api/v1/health│
│  OpenRouter / Ollama / any LLM           │
└──────────────────────────────────────────┘
```

## Customization

Set environment variables on the backend:

```
OPENROUTER_API_KEY=sk-...         # LLM provider
OPENROUTER_MODEL=openai/gpt-4o-mini  # Model to use
SYSTEM_PROMPT="You are..."        # Custom system prompt
```

## License

MIT

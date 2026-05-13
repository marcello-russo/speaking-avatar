<div align="center">
  <h1>🎙️ Speaking Avatar</h1>
  <p><strong>Open source 3D speaking avatar microservice.</strong><br>
  Zero-UI web component — bring your own chat interface.</p>

  <p>
    <a href="https://github.com/marcello-russo/speaking-avatar/stargazers">
      <img src="https://img.shields.io/github/stars/marcello-russo/speaking-avatar?style=flat-square" alt="Stars">
    </a>
    <a href="https://github.com/marcello-russo/speaking-avatar/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
    </a>
    <img src="https://img.shields.io/badge/3D-Three.js-purple?style=flat-square" alt="Three.js">
    <img src="https://img.shields.io/badge/TTS-Edge%20AI-blue?style=flat-square" alt="Edge TTS">
    <img src="https://img.shields.io/badge/LLM-Anthropic%2FOpenAI%2FOllama-green?style=flat-square" alt="LLM">
    <img src="https://img.shields.io/badge/Web_Component-Svelte-orange?style=flat-square" alt="Web Component">
  </p>

  ```html
  <script src="speaking-avatar.umd.js"></script>
  <speaking-avatar></speaking-avatar>
  ```
</div>

---

## ✨ Features

| 🧑 **3D Avatar** | Real-time rendered character with lip-sync, facial expressions, and body gestures (Three.js) |
| 🗣️ **Text-to-Speech** | Natural voices via Microsoft Edge TTS, progressive sentence-level streaming |
| 🧠 **LLM agnostic** | Anthropic, OpenAI-compatible, OpenRouter, Ollama — plug any provider |
| 🧩 **Zero-UI** | Pure avatar, no chat bubbles or FAB built-in. You build the interface, we render the face |
| ⚡ **SSE streaming** | Token-by-token text + concurrent sentence-level audio in a single stream |
| 🐳 **Docker** | `docker compose up` to run the full stack |

## 🚀 Quick Start

### Option 1: Docker (recommended)

```bash
git clone https://github.com/marcello-russo/speaking-avatar
cd speaking-avatar
cp backend/.env.example backend/.env
# Edit backend/.env → add an LLM API key (see below)
docker compose up -d
```

Open **http://localhost:5173** — the avatar renders with a built-in demo UI.

### Option 2: npm / CDN

```bash
npm install speaking-avatar
```

```html
<script src="https://cdn.jsdelivr.net/npm/speaking-avatar/dist/speaking-avatar.umd.js"></script>
<speaking-avatar></speaking-avatar>
```

```javascript
const avatar = document.querySelector('speaking-avatar');
avatar.speak('Hello!');           // TTS
avatar.ask('What is gravity?');   // LLM + TTS
avatar.listen(audioBlob);         // STT
avatar.configure({ ttsApi: '...' });
```

### Option 3: Dev server

```bash
cd web-component && npm run dev     # :5173
cd backend && uvicorn app.main:app  # :8000
```

## ⚙️ Props

| Prop | Default | Description |
|------|---------|-------------|
| `tts-api` | `http://localhost:8000/api/v1` | TTS endpoint base URL |
| `stt-api` | `http://localhost:8000/api/v1/stt` | STT endpoint |
| `llm-api` | `http://localhost:8000/api/v1/chat/stream` | LLM streaming endpoint |
| `voice` | `it-IT-ElsaNeural` | Edge TTS voice |
| `avatar` | `The Coach` | 3D model: `The Coach`, `The Scholar`, `The Mentor`, `The Innovator` |
| `context` | `""` | Course / lesson context passed to the LLM |

### Methods

| Method | Returns | Description |
|--------|---------|-------------|
| `speak(text)` | `Promise<void>` | Speak the given text via TTS |
| `ask(message)` | `Promise<string>` | Send message to LLM via SSE, speak progressively, return full reply |
| `listen(audio)` | `Promise<string>` | Transcribe audio via backend STT |
| `configure(opts)` | `void` | Update props at runtime |

### Events

| Event | Detail | Description |
|-------|--------|-------------|
| `speechstart` | `{ text }` | Avatar started speaking |
| `speechend` | `{ text }` | Avatar finished speaking |
| `viseme` | `{ viseme, time }` | Lip-sync viseme event |
| `error` | `{ error, source }` | Error from LLM, TTS, or STT |

## 🏗️ Backend API

| Route | Method | Description |
|-------|--------|-------------|
| `/api/v1/health` | `GET` | Health check |
| `/api/v1/chat` | `POST` | Non-streaming chat (returns complete reply) |
| `/api/v1/chat/stream` | `POST` | SSE streaming: `token` (text) + `audio_complete` (base64 MP3) events |
| `/api/v1/tts` | `POST` | Text-to-speech (returns MP3 blob) |
| `/api/v1/stt` | `POST` | Speech-to-text (Whisper or mock) |

### SSE event types

```
event: token           {"type":"token","text":"Ciao"}
event: audio_complete  {"type":"audio_complete","seq":0,"data":"<base64>","dur":1.2}
event: done            {"type":"done","session_id":"..."}
```

Audio events include a `seq` counter — the frontend reorders them for correct playback.

### Env vars

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `openrouter` | `anthropic` \| `openai` \| `openrouter` \| `ollama` |
| `ANTHROPIC_API_KEY` | — | Anthropic API key or any Anthropic-compatible (e.g. GLM via `api.z.ai`) |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | Custom endpoint for Anthropic-compatible providers |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Model name |
| `OPENAI_API_KEY` | — | OpenAI / GLM / vLLM / Together / Groq API key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Custom endpoint for OpenAI-compatible providers |
| `OPENAI_MODEL` | `gpt-4o-mini` | Model name |
| `OPENROUTER_API_KEY` | — | OpenRouter API key |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Local Ollama endpoint |
| `OLLAMA_MODEL` | `llama3` | Model name |
| `TTS_VOICE` | `it-IT-ElsaNeural` | Edge TTS voice |
| `STT_ENGINE` | `mock` | `whisper` or `mock` |

## 🧑‍🎨 Custom Avatars

4 pre-built 3D avatars with full skeletal animation and ARKit viseme morph targets:

| Avatar | Personality |
|--------|-------------|
| **The Coach** | Energetic, motivational, direct |
| **The Scholar** | Analytical, detail-oriented, patient |
| **The Mentor** | Encouraging, warm, supportive |
| **The Innovator** | Creative, curious, thought-provoking |

Add custom GLB models with ARKit-standard viseme morph targets.

## 🧪 Local Development

```bash
# Backend
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Web Component
cd web-component && npm install && npm run dev
```

## Architecture

```
SSE stream ──► /chat/stream ──► LLM Provider
                   │
            ┌──────┴──────┐
            │             │
      event "token"   SentenceBuffer → TTS Pipeline
      (text,            (word-aware     (Edge TTS,
       immediate)       boundary,       concurrent,
                        800ms timeout)  seq-numbered)
                              │
                        event "audio_complete"
                        (base64 MP3 + seq + dur)
```

The LLM stream feeds a `SentenceBuffer` that emits complete sentences using adaptive boundary detection (primary `. ! ?`, forced at 80 chars, timeout at 800ms). Each sentence goes to the TTS pipeline which runs Edge TTS concurrently — audio events carry a `seq` field so the frontend can reorder them before playback.

## 📄 License

MIT — use it anywhere, for anything.

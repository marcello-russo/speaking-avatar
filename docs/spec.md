# Speaking Avatar v2 — Design Specification

## 1. Architecture

```
                    ┌──────────────────────────────────────┐
                    │        App dello Sviluppatore         │
                    │  (React, Vue, Moodle, HTML puro, ...) │
                    │                                       │
                    │  ┌────────────────────────────────┐   │
                    │  │  <speaking-avatar>              │   │
                    │  │  .speak(text) → TTS + anima     │   │
                    │  │  .listen(audio) → STT → testo   │   │
                    │  │  .ask(message) → LLM + parla    │   │
                    │  │  .configure(opts)               │   │
                    │  │  onstart, onend, onviseme,      │   │
                    │  │  onerror                        │   │
                    │  └────────┬───────────────────────┘   │
                    └───────────┼───────────────────────────┘
                                │ HTTP
              ┌─────────────────▼──────────────────────┐
              │         Backend (FastAPI)               │
              │  POST /api/v1/tts    → Edge TTS        │
              │  POST /api/v1/stt    → Whisper          │
              │  POST /api/v1/chat   → LLM provider     │
              │  GET  /api/v1/health → OK               │
              │   Docker / Cloud deployment             │
              └──────────────────┬──────────────────────┘
                                 │
              ┌──────────────────▼──────────────────────┐
              │         Provider LLM (configurable)      │
              │  openai → /v1/chat/completions          │
              │     (include vLLM, Together, Groq, ecc) │
              │  anthropic → API Claude                 │
              │  openrouter → hub multi-modello         │
              │  ollama → locale                        │
              └─────────────────────────────────────────┘
```

### 1.1 Key Principles

- **Zero UI**: the web component provides NO chat interface, NO buttons, NO popups. Only the 3D avatar canvas and audio. The developer builds the UI.
- **Black box**: text/audio in → avatar speaks + animates out.
- **Swappable backend**: every API endpoint (TTS, STT, LLM) can be pointed to a custom URL.
- **Self-contained**: CDN script tag + any server with the backend Docker image.

---

## 2. Web Component (`<speaking-avatar>`)

### 2.1 HTML Attributes

| Attribute | Default | Description |
|-----------|---------|-------------|
| `tts-api` | `http://localhost:8000/api/v1/tts` | TTS endpoint URL |
| `stt-api` | `http://localhost:8000/api/v1/stt` | STT endpoint URL |
| `llm-api` | `http://localhost:8000/api/v1/chat` | LLM endpoint URL |
| `voice` | `it-IT-ElsaNeural` | TTS voice name |
| `avatar` | `The Coach` | 3D model identifier |
| `theme` | `light` | `light` or `dark` |

### 2.2 JavaScript API

```js
const el = document.querySelector('speaking-avatar');

// Speak: TTS + 3D animation
await el.speak("Ciao studenti!");

// Listen: STT → transcribed text
const text = await el.listen(audioBlob);
// → "Qual è la formula di Pitagora?"

// Ask: LLM → reply + TTS + animation
const reply = await el.ask("Spiegami la relatività");
// → "La relatività dice che..."

// Runtime configuration
el.configure({
  ttsApi: "https://mio-server.com/tts",
  voice: "en-US-JennyNeural",
});

// Events
el.addEventListener('speechstart', (e) => {
  console.log('Started speaking:', e.detail.text);
});
el.addEventListener('speechend', (e) => {
  console.log('Finished speaking:', e.detail.text);
});
el.addEventListener('viseme', (e) => {
  console.log('Viseme:', e.detail.viseme, e.detail.duration);
});
el.addEventListener('error', (e) => {
  console.error('Error:', e.detail.error, 'Source:', e.detail.source);
});
```

### 2.3 Methods

| Method | Args | Returns | Description |
|--------|------|---------|-------------|
| `speak(text)` | `string` | `Promise<void>` | TTS + animate avatar |
| `listen(audio)` | `Blob | File | FormData` | `Promise<string>` | STT → transcribed text |
| `ask(message)` | `string` | `Promise<string>` | LLM → TTS + animation |
| `configure(opts)` | `object` | `void` | Update runtime config |

### 2.4 Events

| Event | Payload | When |
|-------|---------|------|
| `speechstart` | `{ text }` | Avatar starts speaking |
| `speechend` | `{ text }` | Avatar stops speaking |
| `viseme` | `{ viseme, duration }` | Viseme changes |
| `error` | `{ error, source }` | Any error |

### 2.5 What the Component Does NOT Do

- ❌ No text input / textarea / form
- ❌ No buttons, FAB, popups, or modal
- ❌ No chat bubble UI
- ❌ No session management
- ❌ No conversation history display

All of this is the developer's responsibility. The component is purely an expressive 3D face with voice.

---

## 3. Backend API

### 3.1 Endpoints

| Method | Path | Input | Output |
|--------|------|-------|--------|
| `POST` | `/api/v1/tts` | `{ text, voice? }` | `audio/mpeg` binary |
| `POST` | `/api/v1/stt` | `multipart/form-data` (audio file) | `{ text: string }` |
| `POST` | `/api/v1/chat` | `{ message, context?, session_id? }` | `{ reply, session_id }` |
| `GET` | `/api/v1/health` | — | `{ status, version }` |

### 3.2 TTS — `POST /api/v1/tts`

**Request:**
```json
{
  "text": "Ciao studenti!",
  "voice": "it-IT-ElsaNeural"
}
```

**Response:** `audio/mpeg` binary stream.

**Provider:** Edge TTS by default. The endpoint URL is swappable via the component's `tts-api` attribute.

### 3.3 STT — `POST /api/v1/stt`

**Request:** `multipart/form-data` with an audio file field named `audio`.

**Response:**
```json
{
  "text": "Qual è la formula di Pitagora?"
}
```

**Provider:** Whisper or similar. Endpoint URL swappable.

### 3.4 Chat — `POST /api/v1/chat`

**Request:**
```json
{
  "message": "Spiegami le equazioni",
  "context": "Matematica - Equazioni di secondo grado",
  "session_id": "sess_abc123"
}
```

**Response:**
```json
{
  "reply": "Le equazioni di secondo grado sono...",
  "session_id": "sess_abc123"
}
```

**Context** supports multiple formats:
- Plain string: `"Matematica"`
- Structured: `"Matematica - Equazioni"`
- JSON: `{"course": "Matematica", "lesson": "Equazioni"}`

### 3.5 LLM Provider Configuration

| Provider | `LLM_PROVIDER` env | Required env | Extra optional env |
|----------|-------------------|--------------|-------------------|
| OpenAI-compatible | `openai` | `OPENAI_API_KEY` | `OPENAI_BASE_URL`, `OPENAI_MODEL` |
| Anthropic | `anthropic` | `ANTHROPIC_API_KEY` | `ANTHROPIC_MODEL` |
| OpenRouter | `openrouter` | `OPENROUTER_API_KEY` | `OPENROUTER_MODEL` |
| Ollama | `ollama` | — | `OLLAMA_BASE_URL`, `OLLAMA_MODEL` |

**Default models:**
| Provider | Default model |
|----------|---------------|
| OpenAI-compatible | `gpt-4o-mini` |
| Anthropic | `claude-sonnet-4-20250514` |
| OpenRouter | `openai/gpt-4o-mini` |
| Ollama | `llama3` |

**vLLM note:** vLLM exposes an OpenAI-compatible API. Users set `LLM_PROVIDER=openai`, `OPENAI_BASE_URL` to their vLLM server, and any vLLM-served model as `OPENAI_MODEL`. No separate code needed.

---

## 4. Context System

### 4.1 Context Parsing

The context is parsed by `backend/app/services/context.py` before being sent to the LLM:

- **String** → `"Matematica"` → used as-is
- **Structured string** → `"Matematica - Equazioni"` → split into course/lesson
- **JSON** → `'{"course":"Matematica","lesson":"Equazioni"}'` → parsed into fields
- **URL params** → `?context=...` → passed to component attribute

### 4.2 Prompt Building

```python
def build_prompt(ctx: dict) -> str:
    parts = []
    if ctx["course"]: parts.append(f"Corso: {ctx['course']}")
    if ctx["lesson"]: parts.append(f"Lezione: {ctx['lesson']}")
    context_str = " | ".join(parts) if parts else "Conversazione generale"
    return f"""Sei un tutor AI. Rispondi in modo chiaro.
Contesto: {context_str}"""
```

### 4.3 Session History

- Sessions are identified by `session_id` (random string, generated client-side)
- Backend stores the last 50 messages in memory per session
- History is sent to the LLM with each request (last 6 turns by default)

---

## 5. Moodle Plugin (`moodle-plugin/block_speakingavatar/`)

### 5.1 Structure

```
moodle-plugin/block_speakingavatar/
├── block_speakingavatar.php    # Main block class
├── db/access.php               # Capabilities
├── lang/en/block_speakingavatar.php  # English strings
├── lang/it/block_speakingavatar.php  # Italian strings
├── settings.php                # Plugin settings page
└── version.php                 # Version metadata
```

### 5.2 Behavior

- Adds a floating `💬` button to course pages
- Injects the `<speaking-avatar>` web component into the page (loaded from CDN)
- Reads the course full name from Moodle context and passes it as `context`
- On click, calls `el.ask()` with course context and opens a simple input popup
- Admin settings: backend API URL, default voice, theme, avatar model
- The popup/UI is minimal — just an input field — because the component is purely the avatar face

### 5.3 Settings

| Setting | Key | Default |
|---------|-----|---------|
| Backend API URL | `api_url` | `http://localhost:8000/api/v1` |
| Default voice | `voice` | `it-IT-ElsaNeural` |
| Theme | `theme` | `light` |
| Avatar model | `avatar` | `The Coach` |
| Position | `position` | `right` |

### 5.4 Installation

1. Copy `block_speakingavatar/` into Moodle's `blocks/` directory
2. Visit Site administration → Notifications to install
3. Configure API URL in Settings → Plugins → Blocks → Speaking Avatar
4. Add the block to any course page via "Add a block"

---

## 6. Deploy

### 6.1 Docker (full stack)

```bash
docker compose up -d
# Backend on :8000, web component on :5173 (dev mode)
```

### 6.2 Docker (backend only, production)

```bash
docker build -t speaking-avatar-backend ./backend
docker run -d -p 8000:8000 \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=sk-... \
  speaking-avatar-backend
```

### 6.3 CDN / npm

```bash
cd web-component
npm run build
# Output: dist/speaking-avatar.umd.js and dist/speaking-avatar.es.js
```

Published to npm and available via jsDelivr:
```html
<script src="https://cdn.jsdelivr.net/npm/speaking-avatar/dist/speaking-avatar.umd.js"></script>
```

### 6.4 Integration Examples

**Vanilla HTML:**
```html
<script src="https://cdn.jsdelivr.net/npm/speaking-avatar/dist/speaking-avatar.umd.js"></script>
<speaking-avatar id="tutor"></speaking-avatar>
<script>
  document.getElementById('tutor').speak("Benvenuto!");
</script>
```

**React:**
```jsx
import { useEffect, useRef } from 'react';
import 'speaking-avatar';

function Tutor() {
  const ref = useRef();
  return (
    <div>
      <speaking-avatar ref={ref} />
      <button onClick={() => ref.current.speak("Ciao!")}>Parla</button>
    </div>
  );
}
```

**Moodle (after plugin install):**
Simply add the Speaking Avatar block to any course. No code needed.

---

## 7. File Structure (final)

```
speaking-avatar/
├── web-component/
│   ├── src/
│   │   ├── main.js              # Custom element registration + API
│   │   ├── SpeakingAvatar.svelte # 3D component (refactored, ~200 lines)
│   │   ├── lib/components/chat/
│   │   │   └── AvatarChat.svelte  # Three.js engine (existing, ~2600 lines)
│   │   └── app.css               # Tailwind import
│   ├── static/avatar/            # GLB models (4 avatars + animations)
│   ├── package.json
│   ├── vite.config.js
│   └── Dockerfile
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app
│   │   ├── models/__init__.py   # Pydantic schemas
│   │   ├── routers/
│   │   │   ├── chat.py
│   │   │   └── tts.py
│   │   └── services/
│   │       ├── llm.py           # LLM providers
│   │       ├── tts.py           # Edge TTS
│   │       └── context.py       # Context parser
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
├── moodle-plugin/
│   └── block_speakingavatar/
│       ├── block_speakingavatar.php
│       ├── db/access.php
│       ├── settings.php
│       ├── version.php
│       └── lang/en|it/...
├── docker-compose.yml
├── docs/spec.md
└── README.md
```

---

## 8. Out of Scope (v1)

- RAG su documenti
- Streaming SSE per chat
- Classroom background 3D
- Locomotion/dance animations
- Test automation
- CI/CD pipeline

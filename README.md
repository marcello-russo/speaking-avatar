<div align="center">
  <h1>🎙️ Speaking Avatar</h1>
  <p><strong>Open source 3D speaking avatar microservice.</strong><br>
  Drop-in web component for AI-powered conversational interfaces.</p>

  <p>
    <a href="https://github.com/marcello-russo/speaking-avatar/stargazers">
      <img src="https://img.shields.io/github/stars/marcello-russo/speaking-avatar?style=flat-square" alt="Stars">
    </a>
    <a href="https://github.com/marcello-russo/speaking-avatar/blob/main/LICENSE">
      <img src="https://img.shields.io/badge/license-MIT-blue?style=flat-square" alt="License">
    </a>
    <img src="https://img.shields.io/badge/3D-Three.js-purple?style=flat-square" alt="Three.js">
    <img src="https://img.shields.io/badge/TTS-Edge%20AI-blue?style=flat-square" alt="Edge TTS">
    <img src="https://img.shields.io/badge/LLM-OpenRouter%2FOllama-green?style=flat-square" alt="LLM">
    <img src="https://img.shields.io/badge/Web_Component-Svelte-orange?style=flat-square" alt="Web Component">
  </p>

  <img src="https://placehold.co/800x400/6366f1/white?text=3D+Speaking+Avatar" width="600" alt="demo">

  <br>

  ```html
  <script type="module" src="speaking-avatar.js"></script>
  <speaking-avatar context="Mathematics" accent="#6366f1"></speaking-avatar>
  ```
</div>

---

## ✨ Features

| 🧑 **3D Avatar** | Real-time rendered character with lip-sync, facial expressions, and body gestures (Three.js) |
| 🗣️ **Text-to-Speech** | Natural voices in 100+ languages via Microsoft Edge TTS |
| 🧠 **AI-Powered** | Connects to OpenRouter, Ollama, or any OpenAI-compatible API |
| 🧩 **Web Component** | Works in any framework — React, Vue, Angular, Moodle, WordPress, plain HTML |
| 🎨 **Customizable** | Accent color, theme, avatar model, camera position, system prompt |
| 🐳 **Docker** | `docker compose up` to run the full stack |

## 🚀 Quick Start

### Option 1: Docker (recommended — full stack)

```bash
git clone https://github.com/marcello-russo/speaking-avatar
cd speaking-avatar
cp backend/.env.example backend/.env
# Edit backend/.env → add your OPENROUTER_API_KEY
docker compose up -d
```

Open **http://localhost:5173** → click 💬 to chat.

### Option 2: Import in your app (2 lines)

```html
<script type="module" src="http://localhost:5173/src/main.js"></script>
<speaking-avatar context="Mathematics" accent="#6366f1"></speaking-avatar>
```

> The web component auto-registers. Just add the `<script>` tag and the `<speaking-avatar>` element anywhere in your HTML.

### Option 3: Self-hosted build

```bash
cd web-component
npm run build
npx serve dist    # or any static file server
```

```html
<script src="https://your-cdn.com/speaking-avatar.umd.js"></script>
<speaking-avatar context="Biology" theme="light"></speaking-avatar>
```

## 📦 Integration

The `<speaking-avatar>` web component works in any framework. Here's how to use it:

### Vanilla HTML

```html
<!doctype html>
<html>
<head>
  <script type="module" src="http://localhost:5173/src/main.js"></script>
</head>
<body>
  <speaking-avatar context="Mathematics" theme="light"></speaking-avatar>
</body>
</html>
```

### React

```jsx
function App() {
  useEffect(() => {
    import('http://localhost:5173/src/main.js');
  }, []);
  return <speaking-avatar context="Physics" accent="#10b981" />;
}
```

### Vue

```vue
<template>
  <speaking-avatar context="Chemistry" theme="dark" />
</template>
<script setup>
  onMounted(() => import('http://localhost:5173/src/main.js'));
</script>
```

### Moodle (add as HTML block)

In any course page, add a Custom HTML block:

```html
<a href="http://localhost:5173/?course=Mathematics" class="btn btn-primary" target="_blank">
  🎓 Study with AI Tutor
</a>
```

### Passing context (documents, files)

```html
<!-- Single context -->
<speaking-avatar context="Linear Algebra - Chapter 3"></speaking-avatar>

<!-- Multiple documents (URL-encoded JSON) -->
<speaking-avatar
  context='[{"title":"Chapter 1","url":"https://..."},{"title":"Notes","url":"https://..."}]'
></speaking-avatar>
```

## 🎮 Props

| Prop | Default | Description |
|------|---------|-------------|
| `context` | `""` | Context passed to the AI (course name, topic, etc.) |
| `theme` | `"light"` | `"light"` or `"dark"` |
| `accent` | `"#6366f1"` | Accent color for UI elements |
| `apiurl` | `"http://localhost:8000/api/v1"` | Backend API base URL |
| `avatar` | `"The Coach"` | 3D avatar model: `The Coach`, `The Scholar`, `The Mentor`, `The Innovator` |
| `title` | `"AI Tutor"` | Title shown in chat header |
| `fab` | `"true"` | Show/hide the floating action button |

## ⚙️ Backend API

| Route | Method | Description |
|-------|--------|-------------|
| `/api/v1/health` | `GET` | Health check |
| `/api/v1/chat` | `POST` | Send a message to the AI |
| `/api/v1/tts` | `POST` | Convert text to speech (returns MP3) |

### Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | — | API key for OpenRouter (or any OpenAI-compatible provider) |
| `OPENROUTER_MODEL` | `openai/gpt-4o-mini` | Model to use |
| `SYSTEM_PROMPT` | Custom | System prompt for the AI |

## 🏗️ Architecture

```
┌──────────────────────────────────────────┐
│          <speaking-avatar>               │
│  HTML Web Component                      │
│  ├── Three.js 3D renderer               │
│  ├── Edge TTS audio playback             │
│  └── Floating chat UI                    │
└─────────────────┬────────────────────────┘
                  │ REST API
┌─────────────────▼────────────────────────┐
│          FastAPI Backend                 │
│  /api/v1/chat  /api/v1/tts  /health     │
│  OpenRouter / Ollama / any LLM API       │
└──────────────────────────────────────────┘
```

## 🧑‍🎨 Custom Avatars

The project includes 4 pre-built 3D avatars with full skeletal animation and facial visemes:

| Avatar | Personality |
|--------|-------------|
| **The Coach** | Energetic, motivational, direct |
| **The Scholar** | Analytical, detail-oriented, patient |
| **The Mentor** | Encouraging, warm, supportive |
| **The Innovator** | Creative, curious, thought-provoking |

You can add custom GLB models — the engine supports any model with a compatible skeleton and viseme morph targets (ARKit standard).

## 🧪 Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Web Component
cd web-component
npm install
npm run dev
```

## 📄 License

MIT — use it anywhere, for anything.

---

<div align="center">
  <p>Built with ❤️ for open source AI</p>
  <p>
    <a href="https://github.com/marcello-russo/speaking-avatar/issues">Report a bug</a>
    ·
    <a href="https://github.com/marcello-russo/speaking-avatar/discussions">Discussion</a>
  </p>
</div>

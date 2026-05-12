# Speaking Avatar v2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Refactor the speaking-avatar from a chat-widget with 3 modes into a zero-UI web component that exposes `.speak()`, `.listen()`, `.ask()` — a pure 3D face with voice.

**Architecture:** Web component (Svelte + Three.js) loads as CDN script. Backend (FastAPI + edge-tts) provides TTS, STT, and LLM endpoints. LLM supports 4 providers (OpenAI-compatible, Anthropic, OpenRouter, Ollama). Moodle plugin injects the component with course context.

**Tech Stack:** Svelte 5, Three.js, FastAPI, edge-tts, OpenAI SDK, Anthropic SDK, Whisper

---

## File Structure

| File | Status | Responsibility |
|------|--------|---------------|
| `web-component/src/SpeakingAvatar.svelte` | **MODIFY** | Zero-UI component: canvas + `.speak()`/`.listen()`/`.ask()`/`.configure()` + events |
| `web-component/src/main.js` | **MODIFY** | Custom element registration, attribute reading |
| `web-component/index.html` | **MODIFY** | Demo page with new API |
| `web-component/package.json` | **MODIFY** | npm-ready package metadata |
| `backend/app/services/llm.py` | **MODIFY** | Add OpenAI-compatible + Anthropic providers |
| `backend/app/routers/stt.py` | **CREATE** | POST /api/v1/stt with Whisper |
| `backend/app/main.py` | **MODIFY** | Register STT router |
| `backend/requirements.txt` | **MODIFY** | Add openai, anthropic, faster-whisper |
| `moodle-plugin/block_speakingavatar/block_speakingavatar.php` | **CREATE** | Moodle block main class |
| `moodle-plugin/block_speakingavatar/db/access.php` | **CREATE** | Moodle capabilities |
| `moodle-plugin/block_speakingavatar/settings.php` | **CREATE** | Admin settings page |
| `moodle-plugin/block_speakingavatar/version.php` | **CREATE** | Version metadata |
| `moodle-plugin/block_speakingavatar/lang/en/block_speakingavatar.php` | **CREATE** | English strings |
| `moodle-plugin/block_speakingavatar/lang/it/block_speakingavatar.php` | **CREATE** | Italian strings |
| `docs/spec.md` | **EXISTS** | Design spec (already written) |

---

### Task 1: Web Component — Zero-UI Refactor

**Files:**
- Modify: `web-component/src/SpeakingAvatar.svelte` (full rewrite)
- Modify: `web-component/src/main.js`
- Test: Open `index.html` after restart

This task removes all chat UI, FAB, popups, and modes. The component becomes a pure 3D canvas with a JavaScript API.

- [ ] **Step 1: Rewrite SpeakingAvatar.svelte**

Replace the entire file with:

```svelte
<script lang="ts">
  import { onMount, onDestroy, createEventDispatcher } from 'svelte';
  import AvatarChat from '$lib/components/chat/AvatarChat.svelte';

  const dispatch = createEventDispatcher();

  export let ttsApi: string = 'http://localhost:8000/api/v1/tts';
  export let sttApi: string = 'http://localhost:8000/api/v1/stt';
  export let llmApi: string = 'http://localhost:8000/api/v1/chat';
  export let voice: string = 'it-IT-ElsaNeural';
  export let avatar: string = 'The Coach';

  let currentMessage = '';
  let speaking = false;

  // ── Public API ──────────────────────────────────────

  export async function speak(text: string): Promise<void> {
    return new Promise((resolve, reject) => {
      currentMessage = text;
      speaking = true;
      const handler = () => {
        removeEventListener('speechend', handler);
        resolve();
      };
      addEventListener('speechend', handler);

      speakViaApi(text).catch(reject);
    });
  }

  export async function listen(audio: Blob | File): Promise<string> {
    const form = new FormData();
    form.append('audio', audio);
    const res = await fetch(sttApi, { method: 'POST', body: form });
    if (!res.ok) { dispatch('error', { error: 'STT failed', source: 'stt' }); throw new Error('STT failed'); }
    const data = await res.json();
    return data.text;
  }

  export async function ask(message: string): Promise<string> {
    const res = await fetch(llmApi, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    if (!res.ok) { dispatch('error', { error: 'LLM failed', source: 'llm' }); throw new Error('LLM failed'); }
    const data = await res.json();
    await speak(data.reply);
    return data.reply;
  }

  export function configure(opts: Record<string, string>): void {
    if (opts.ttsApi) ttsApi = opts.ttsApi;
    if (opts.sttApi) sttApi = opts.sttApi;
    if (opts.llmApi) llmApi = opts.llmApi;
    if (opts.voice) voice = opts.voice;
    if (opts.avatar) avatar = opts.avatar;
  }

  // ── Internal TTS ────────────────────────────────────

  async function speakViaApi(text: string) {
    dispatch('speechstart', { text });
    try {
      const res = await fetch(ttsApi, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, voice }),
      });
      if (!res.ok) throw new Error('TTS failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        speaking = false;
        dispatch('speechend', { text });
      };
      audio.play();
    } catch (e) {
      dispatch('error', { error: String(e), source: 'tts' });
      speaking = false;
    }
  }

  // ── Lifecycle ───────────────────────────────────────

  onMount(() => {
    // Set the global API base so AvatarChat's TTS uses our endpoint
    (window as any).__SPEAKING_AVATAR_API__ = ttsApi.replace('/tts', '');
  });
</script>

<div class="sa-root">
  {#key avatar}
    <AvatarChat
      {currentMessage}
      {speaking}
      useClassroom={false}
      on:speechend={() => { /* already handled in speak() */ }}
    />
  {/key}
</div>

<style>
  .sa-root { width: 100%; height: 100%; position: relative; }
  .sa-root :global(canvas) { width: 100% !important; height: 100% !important; }
</style>
```

- [ ] **Step 2: Update main.js**

```js
import { mount } from 'svelte';
import SpeakingAvatar from './SpeakingAvatar.svelte';

class SpeakingAvatarElement extends HTMLElement {
  connectedCallback() {
    const props = {
      ttsApi: this.getAttribute('tts-api') || this.getAttribute('ttsapi') || 'http://localhost:8000/api/v1/tts',
      sttApi: this.getAttribute('stt-api') || this.getAttribute('sttapi') || 'http://localhost:8000/api/v1/stt',
      llmApi: this.getAttribute('llm-api') || this.getAttribute('llmapi') || 'http://localhost:8000/api/v1/chat',
      voice: this.getAttribute('voice') || 'it-IT-ElsaNeural',
      avatar: this.getAttribute('avatar') || 'The Coach',
    };

    this.style.display = 'block';
    this.style.width = '100%';
    this.style.height = '100%';

    const inst = mount(SpeakingAvatar, { target: this, props });

    // Proxy methods from element to component instance
    this.speak = inst.speak;
    this.listen = inst.listen;
    this.ask = inst.ask;
    this.configure = inst.configure;
  }
}

customElements.define('speaking-avatar', SpeakingAvatarElement);
export default SpeakingAvatarElement;
```

- [ ] **Step 3: Update demo index.html**

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Speaking Avatar — Demo</title>
  <style>
    body { margin: 0; font-family: sans-serif; display: flex; height: 100vh; }
    #avatar-panel { flex: 1; position: relative; background: #f8f9fc; }
    #controls { width: 360px; padding: 2rem; display: flex; flex-direction: column; gap: 1rem; background: white; border-left: 1px solid #e2e8f0; }
    textarea, input, button { padding: .5rem; font-size: .875rem; border-radius: 8px; border: 1px solid #cbd5e1; }
    button { background: #6366f1; color: white; border: none; cursor: pointer; }
    button:hover { opacity: .85; }
    #log { font-size: .75rem; color: #64748b; max-height: 300px; overflow-y: auto; font-family: monospace; }
  </style>
</head>
<body>
  <div id="avatar-panel">
    <speaking-avatar id="tutor"></speaking-avatar>
  </div>
  <div id="controls">
    <h2 style="margin:0;">Speaking Avatar Demo</h2>
    <textarea id="text-input" rows="3" placeholder="Type something...">Ciao! Oggi studiamo le equazioni di secondo grado.</textarea>
    <button id="btn-speak">🗣️ Speak</button>
    <button id="btn-ask">🤖 Ask AI</button>
    <div id="log"></div>
  </div>
  <script type="module" src="/src/main.js"></script>
  <script>
    const tutor = document.getElementById('tutor');
    const input = document.getElementById('text-input');
    const log = document.getElementById('log');

    function logMsg(msg) { log.textContent += '> ' + msg + '\n'; log.scrollTop = log.scrollHeight; }

    document.getElementById('btn-speak').onclick = async () => {
      await tutor.speak(input.value);
      logMsg('Spoken: ' + input.value.slice(0, 40) + '...');
    };

    document.getElementById('btn-ask').onclick = async () => {
      logMsg('Asking AI...');
      const reply = await tutor.ask(input.value);
      logMsg('AI replied: ' + reply.slice(0, 60) + '...');
    };

    tutor.addEventListener('speechstart', (e) => logMsg('Start: ' + e.detail.text.slice(0, 30) + '...'));
    tutor.addEventListener('speechend', (e) => logMsg('End'));
    tutor.addEventListener('error', (e) => logMsg('Error: ' + e.detail.error));
  </script>
</body>
</html>
```

- [ ] **Step 4: Restart and verify**

```bash
kill $(lsof -t -i:5173) 2>/dev/null; sleep 1
cd /home/marcello/Documenti/prevedo/speaking-avatar/web-component
nohup npx vite --host > /tmp/vite-avatar.log 2>&1 &
sleep 3
curl -s http://localhost:5173/ | head -5
```

Expected: Page loads with avatar on left, controls on right.

- [ ] **Step 5: Commit**

```bash
cd /home/marcello/Documenti/prevedo/speaking-avatar
git add web-component/src/SpeakingAvatar.svelte web-component/src/main.js web-component/index.html
git commit -m "feat: zero-UI web component with speak/listen/ask API"
```

---

### Task 2: Backend — Add STT Endpoint

**Files:**
- Create: `backend/app/routers/stt.py`
- Modify: `backend/app/main.py`
- Modify: `backend/requirements.txt`
- Test: `curl` with audio file

- [ ] **Step 1: Create STT router**

```python
# backend/app/routers/stt.py
import os, tempfile
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

STT_ENGINE = os.getenv("STT_ENGINE", "whisper")

@router.post("/stt")
async def speech_to_text(audio: UploadFile = File(...)):
    if STT_ENGINE == "whisper":
        return await _whisper_stt(audio)
    return await _mock_stt(audio)

async def _whisper_stt(audio: UploadFile) -> dict:
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("base", device="cpu", compute_type="int8")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(await audio.read())
            tmp_path = tmp.name
        segments, _ = model.transcribe(tmp_path, language="it")
        text = " ".join(seg.text for seg in segments)
        os.unlink(tmp_path)
        return {"text": text or ""}
    except ImportError:
        return await _mock_stt(audio)

async def _mock_stt(audio: UploadFile) -> dict:
    # Silently read and discard audio, return mock
    await audio.read()
    return {"text": "Testo da riconoscimento vocale"}
```

- [ ] **Step 2: Register STT router in main.py**

```python
# backend/app/main.py — add import and registration
from app.routers import chat, tts, stt  # add stt
app.include_router(stt.router, prefix="/api/v1")  # add this line
```

- [ ] **Step 3: Add whisper to requirements**

```
faster-whisper>=1.1.0
```

- [ ] **Step 4: Restart backend and test**

```bash
kill -9 $(lsof -t -i:8000) 2>/dev/null; sleep 1
cd /home/marcello/Documenti/prevedo/speaking-avatar/backend
source venv/bin/activate && pip install -r requirements.txt -q
nohup ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend-llm.log 2>&1 &
sleep 4
curl -s -X POST http://localhost:8000/api/v1/stt -F "audio=@/dev/null" | python3 -m json.tool
```

Expected: `{ "text": "Testo da riconoscimento vocale" }` (mock, since no real audio).

- [ ] **Step 5: Commit**

```bash
cd /home/marcello/Documenti/prevedo/speaking-avatar
git add backend/app/routers/stt.py backend/app/main.py backend/requirements.txt
git commit -m "feat: add STT endpoint with Whisper support"
```

---

### Task 3: Backend — Add OpenAI-compatible and Anthropic LLM Providers

**Files:**
- Modify: `backend/app/services/llm.py`
- Modify: `backend/requirements.txt`
- Modify: `backend/.env.example`

- [ ] **Step 1: Update llm.py with OpenAI and Anthropic providers**

```python
# backend/app/services/llm.py — add after existing imports
import os, httpx

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openrouter")

# OpenAI-compatible
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

# OpenRouter (existing)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")

# Ollama (existing)
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")
```

- [ ] **Step 2: Add dispatcher and provider functions**

Add after `build_prompt`:

```python
async def chat(message: str, ctx: dict, history: list | None = None) -> str:
    prompt = build_prompt(ctx)
    if LLM_PROVIDER == "ollama":
        return await _ollama(message, prompt)
    elif LLM_PROVIDER == "anthropic":
        return await _anthropic(message, prompt, history)
    elif LLM_PROVIDER == "openai":
        return await _openai_compat(message, prompt, history)
    else:
        return await _openrouter(message, prompt, history)


async def _openai_compat(message: str, prompt: str, history: list | None = None) -> str:
    if not OPENAI_API_KEY:
        return _fallback(message)
    messages = [{"role": "system", "content": prompt}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": message})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": OPENAI_MODEL, "messages": messages},
            )
            data = resp.json()
            return data["choices"][0]["message"]["content"]
    except Exception:
        return _fallback(message)


async def _anthropic(message: str, prompt: str, history: list | None = None) -> str:
    if not ANTHROPIC_API_KEY:
        return _fallback(message)
    system = prompt
    messages_list = []
    if history:
        messages_list.extend(history[-6:])
    messages_list.append({"role": "user", "content": message})
    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                json={"model": ANTHROPIC_MODEL, "system": system, "messages": messages_list, "max_tokens": 2048},
            )
            data = resp.json()
            return data["content"][0]["text"]
    except Exception:
        return _fallback(message)


# Keep existing _openrouter, _ollama, _fallback unchanged
```

Note: Remove the old top-level `async def chat()` function and replace with the new dispatcher above. Keep `_openrouter`, `_ollama`, and `_fallback` as-is.

- [ ] **Step 3: Update requirements.txt**

```
openai>=1.0.0
anthropic>=0.50.0
```

(These are optional — only needed if using those providers. httpx already handles the API calls.)

- [ ] **Step 4: Update .env.example**

```env
# Provider: openai | anthropic | openrouter | ollama
LLM_PROVIDER=openrouter

# OpenAI-compatible (also covers vLLM, Together, Groq, etc.)
OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini

# Anthropic
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# OpenRouter
OPENROUTER_API_KEY=
OPENROUTER_MODEL=openai/gpt-4o-mini

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3

# STT
STT_ENGINE=whisper

# TTS (uses built-in edge-tts by default)
```

- [ ] **Step 5: Restart and test**

```bash
kill -9 $(lsof -t -i:8000) 2>/dev/null; sleep 2
cd /home/marcello/Documenti/prevedo/speaking-avatar/backend
source venv/bin/activate && pip install -r requirements.txt -q
nohup ./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/backend-llm.log 2>&1 &
sleep 3
curl -s http://localhost:8000/api/v1/health | python3 -m json.tool
```

Expected: `{ "status": "ok", "version": "1.0.0" }`

- [ ] **Step 6: Commit**

```bash
cd /home/marcello/Documenti/prevedo/speaking-avatar
git add backend/app/services/llm.py backend/requirements.txt backend/.env.example
git commit -m "feat: add OpenAI-compatible and Anthropic LLM providers"
```

---

### Task 4: Moodle Plugin

**Files — all CREATE:**
- `moodle-plugin/block_speakingavatar/block_speakingavatar.php`
- `moodle-plugin/block_speakingavatar/db/access.php`
- `moodle-plugin/block_speakingavatar/settings.php`
- `moodle-plugin/block_speakingavatar/version.php`
- `moodle-plugin/block_speakingavatar/lang/en/block_speakingavatar.php`
- `moodle-plugin/block_speakingavatar/lang/it/block_speakingavatar.php`

- [ ] **Step 1: Create main block class**

```php
<?php
// moodle-plugin/block_speakingavatar/block_speakingavatar.php

class block_speakingavatar extends block_base {
    public function init() {
        $this->title = get_string('pluginname', 'block_speakingavatar');
    }

    public function get_content() {
        global $COURSE, $CFG;

        if ($this->content !== null) {
            return $this->content;
        }

        $apiurl = get_config('block_speakingavatar', 'api_url') ?: 'http://localhost:8000/api/v1';
        $voice = get_config('block_speakingavatar', 'voice') ?: 'it-IT-ElsaNeural';
        $theme = get_config('block_speakingavatar', 'theme') ?: 'light';
        $avatar = get_config('block_speakingavatar', 'avatar') ?: 'The Coach';
        $coursename = $COURSE->fullname ?? '';

        $this->content = new stdClass();
        $this->content->text = '
<div id="speaking-avatar-mount"></div>
<script src="https://cdn.jsdelivr.net/npm/speaking-avatar/dist/speaking-avatar.umd.js"></script>
<script>
(function() {
  var el = document.createElement("speaking-avatar");
  el.setAttribute("tts-api", "' . $apiurl . '/tts");
  el.setAttribute("stt-api", "' . $apiurl . '/stt");
  el.setAttribute("llm-api", "' . $apiurl . '/chat");
  el.setAttribute("voice", "' . $voice . '");
  el.setAttribute("avatar", "' . $avatar . '");
  el.style.position = "fixed";
  el.style.bottom = "20px";
  el.style.right = "20px";
  el.style.width = "80px";
  el.style.height = "120px";
  el.style.zIndex = "9999";
  el.style.cursor = "pointer";
  el.style.borderRadius = "12px";
  el.style.boxShadow = "0 4px 20px rgba(0,0,0,0.15)";
  el.style.background = "' . ($theme === 'dark' ? '#1a1a2e' : 'white') . '";
  el.style.transition = "all 0.3s ease";

  var expanded = false;
  el.addEventListener("click", function() {
    expanded = !expanded;
    if (expanded) {
      el.style.width = "360px";
      el.style.height = "500px";
      el.style.bottom = "20px";
      el.style.right = "20px";
      el.style.borderRadius = "16px";
      el.speak("Benvenuto al corso ' . addslashes($coursename) . '! Cosa vuoi studiare?");
    } else {
      el.style.width = "80px";
      el.style.height = "120px";
      el.style.borderRadius = "12px";
    }
  });

  document.getElementById("speaking-avatar-mount").appendChild(el);
})();
</script>';
        $this->content->footer = '';

        return $this->content;
    }

    public function applicable_formats() {
        return array('course-view' => true, 'site' => false);
    }

    public function has_config() {
        return true;
    }
}
```

- [ ] **Step 2: Create db/access.php**

```php
<?php
// moodle-plugin/block_speakingavatar/db/access.php
defined('MOODLE_INTERNAL') || die();
$capabilities = array(
    'block/speakingavatar:addinstance' => array(
        'riskbitmask' => RISK_SPAM,
        'captype' => 'write',
        'contextlevel' => CONTEXT_BLOCK,
        'archetypes' => array('editingteacher' => CAP_ALLOW, 'manager' => CAP_ALLOW),
    ),
);
```

- [ ] **Step 3: Create settings.php**

```php
<?php
// moodle-plugin/block_speakingavatar/settings.php
if ($hassiteconfig) {
    $settings = new admin_settingpage('block_speakingavatar', get_string('pluginname', 'block_speakingavatar'));
    $settings->add(new admin_setting_configtext('block_speakingavatar/api_url',
        get_string('api_url', 'block_speakingavatar'),
        get_string('api_url_desc', 'block_speakingavatar'),
        'http://localhost:8000/api/v1', PARAM_URL));
    $settings->add(new admin_setting_configtext('block_speakingavatar/voice',
        get_string('voice', 'block_speakingavatar'), '', 'it-IT-ElsaNeural', PARAM_TEXT));
    $settings->add(new admin_setting_configselect('block_speakingavatar/theme',
        get_string('theme', 'block_speakingavatar'), '', 'light',
        array('light' => 'Light', 'dark' => 'Dark')));
    $settings->add(new admin_setting_configtext('block_speakingavatar/avatar',
        get_string('avatar', 'block_speakingavatar'), '', 'The Coach', PARAM_TEXT));
    $ADMIN->add('blocksettings', $settings);
}
```

- [ ] **Step 4: Create version.php**

```php
<?php
// moodle-plugin/block_speakingavatar/version.php
defined('MOODLE_INTERNAL') || die();
$plugin->component = 'block_speakingavatar';
$plugin->version = 2026051100;
$plugin->requires = 2021051700;  // Moodle 4.0+
$plugin->maturity = MATURITY_STABLE;
$plugin->release = '1.0.0';
```

- [ ] **Step 5: Create English language file**

```php
<?php
// moodle-plugin/block_speakingavatar/lang/en/block_speakingavatar.php
$string['pluginname'] = 'Speaking Avatar';
$string['api_url'] = 'Backend API URL';
$string['api_url_desc'] = 'Base URL of the Speaking Avatar backend (e.g. http://localhost:8000/api/v1)';
$string['voice'] = 'TTS Voice';
$string['theme'] = 'Theme';
$string['avatar'] = 'Avatar Model';
$string['speakingavatar:addinstance'] = 'Add a new Speaking Avatar block';
```

- [ ] **Step 6: Create Italian language file**

```php
<?php
// moodle-plugin/block_speakingavatar/lang/it/block_speakingavatar.php
$string['pluginname'] = 'Speaking Avatar';
$string['api_url'] = 'URL Backend API';
$string['api_url_desc'] = 'URL del backend Speaking Avatar (es. http://localhost:8000/api/v1)';
$string['voice'] = 'Voce TTS';
$string['theme'] = 'Tema';
$string['avatar'] = 'Modello Avatar';
$string['speakingavatar:addinstance'] = 'Aggiungere un block Speaking Avatar';
```

- [ ] **Step 7: Commit**

```bash
cd /home/marcello/Documenti/prevedo/speaking-avatar
git add moodle-plugin/
git commit -m "feat: add Moodle block plugin for Speaking Avatar"
```

---

### Task 5: npm/CDN Build Configuration

**Files:**
- Modify: `web-component/package.json`

- [ ] **Step 1: Update package.json for npm publish**

Key changes:
- `"name": "speaking-avatar"` is ready (already set)
- `"private": false` for npm publish
- Add `"files"` field to include dist/ and README

```json
{
  "name": "speaking-avatar",
  "version": "1.0.0",
  "type": "module",
  "private": false,
  "description": "Open source 3D speaking avatar web component. Zero UI — just a 3D face with voice.",
  "keywords": ["avatar", "3d", "tts", "stt", "llm", "web-component", "threejs"],
  "license": "MIT",
  "repository": "marcello-russo/speaking-avatar",
  "files": ["dist/", "README.md"],
  "main": "dist/speaking-avatar.umd.js",
  "module": "dist/speaking-avatar.es.js",
  "scripts": {
    "dev": "vite",
    "build": "vite build && cp -r static dist/static",
    "preview": "vite preview",
    "prepublishOnly": "npm run build"
  },
  "devDependencies": {
    "@sveltejs/vite-plugin-svelte": "^7.1.2",
    "@tailwindcss/vite": "^4.3.0",
    "svelte": "^5.55.5",
    "tailwindcss": "^4.3.0",
    "vite": "^8.0.12"
  },
  "dependencies": {
    "three": "^0.174.0"
  }
}
```

- [ ] **Step 2: Build and verify**

```bash
cd /home/marcello/Documenti/prevedo/speaking-avatar/web-component
npm run build
ls -la dist/
```

Expected output:
```
dist/
  speaking-avatar.umd.js   (~666KB)
  speaking-avatar.es.js    (~666KB)
  avatar-webapp.css        (~4KB)
  static/avatar/           (GLB models + animations)
```

- [ ] **Step 3: Commit**

```bash
cd /home/marcello/Documenti/prevedo/speaking-avatar
git add web-component/package.json
git commit -m "chore: configure npm/CDN build and publish"
```

---

### Task 6: Final Cleanup

**Files:**
- Remove: `web-component/src/app.css` (Tailwind import not needed — we use no Tailwind classes now)
- Remove old unused files

- [ ] **Step 1: Remove unused files**

```bash
rm -f /home/marcello/Documenti/prevedo/speaking-avatar/web-component/src/app.css
```

- [ ] **Step 2: Verify cleanup**

Ensure no `.bak`, no `PrevedoAvatar.svelte`, no stale files in the component.

- [ ] **Step 3: Final commit**

```bash
cd /home/marcello/Documenti/prevedo/speaking-avatar
git add -A
git status  # verify only intended changes
git commit -m "chore: cleanup unused files and finalize v2 refactor"
git push
```

---

## Spec Coverage Check

| Spec Section | Covered By |
|-------------|------------|
| 2.1-2.5 Web Component (zero UI, API, events) | Task 1 |
| 3.1-3.4 Backend API (TTS, STT, Chat) | Task 1 (TTS), Task 2 (STT) |
| 3.5 LLM Provider Configuration | Task 3 |
| 4.1-4.3 Context System | Already implemented in existing `context.py` |
| 5.1-5.4 Moodle Plugin | Task 4 |
| 6.1-6.4 Deploy (npm/CDN) | Task 5 |
| 7. File Structure | Tasks 1-6 |
| 8. Out of Scope | Not implemented (by design) |

# LLM → TTS Streaming Pipeline Design

## Goal

Replace today's sequential flow (LLM complete → TTS complete → play) with a concurrent streaming pipeline where TTS starts generating and delivering audio while the LLM is still producing tokens.

## Architecture Overview

```
                    ┌──────────────┐
User ──► SSE ──►    │  /chat/stream│◄──── httpx.stream ──── LLM Provider
                    └──────┬───────┘
                           │
                    token per token (SSE)
                           │
              ┌────────────┼──────────────────┐
              ▼            ▼                   ▼
      event "token"   SentenceBuffer      Audio Pipeline
      (texto,         (accumula,          (Edge TTS stream +
       immediato)      detecta boundary)   cache + viseme calc)
                           │                   │
                      frase completa      chunk audio MP3
                           │                   │
                      ────► TtsPipeline ────────┘
                           │
                    unified SSE event
                           │
              ┌────────────┼──────────────┐
              ▼            ▼              ▼
         "token"      "audio"         "done"
         (testo)      (base64+"dur")   (fine)
```

## Backend Components

### 1. SentenceBuffer

File: `backend/app/services/sentence_buffer.py`

Responsabilità:
- Riceve token in ingresso dalla SSE stream
- Applica boundary detection adattivo
- Emette frasi complete non appena pronte

**Boundary logic:**
```
soglia_base = 80 caratteri
backpressure = TtsPipeline.queue_depth()
soglia_effettiva = soglia_base + (backpressure * 30)

se buffer contiene boundary primario (. ! ?):
  emetti frase IMMEDIATO
altrimenti se buffer >= soglia_effettiva:
  emetti frase FORZATO
altrimenti timeout >= 3s dal primo token:
  emetti frase TIMEOUT

su flush (evento done): emetti resto del buffer
```

**Zero-copy design:** il buffer mantiene solo indici (offset, lunghezza) nel token stream. Le stringhe vengono materializzate solo quando si emette la frase, non a ogni push.

### 2. TtsPipeline

File: `backend/app/services/tts_pipeline.py`

Responsabilità:
- Riceve frasi da SentenceBuffer
- Avvia Edge TTS streaming per ogni frase (in parallelo tra loro)
- Calcola viseme timing dalla durata audio reale
- Gestisce coda: frasi successive aspettano che la precedente abbia iniziato a suonare

**Flusso per frase:**

```
SentenceBuffer emette "Ciao come stai?"
  │
  ├─ AudioCache.get("ciao come stai")
  │   ├─ hit → callback con chunk audio cachati
  │   └─ miss → edge_tts.Communicate("Ciao come stai?", voce).stream()
  │               │
  │               per ogni chunk {"type":"audio", "data": bytes}:
  │                 durata = len(data) / sample_rate
  │                 viseme_timing = distribuisci su durata
  │                 callback(chunk base64, durata, visemi)
  │               │
  │               └─ salva in AudioCache
  │
  └─ callback emette evento SSE "audio"
```

**Viseme timing da durata reale:**

Attualmente distribuzione uniforme sulla lunghezza del testo. Con la durata audio reale:

```python
ratio = len(testo_frase) / durata_totale_frase  # caratteri al secondo
viseme_count = numero_caratteri_parlati
time_per_char = durata_totale_frase / viseme_count

visemi = [
    {"index": viseme_index, "time": i * time_per_char}
    for i, c in enumerate(testo_parlato)
]
```

### 3. AudioCache

File: `backend/app/services/audio_cache.py`

Cache L1 (in-memory): `dict[str, list[dict]]` — max 20 entry, LRU eviction
  Chiave: hash MD5 del testo normalizzato
  Valore: lista di chunk {"data": bytes, "dur": float}

Cache L2 (file): `data/tts-cache/` — frasi pre-generate all'avvio
  `greeting.json`, `dont-know.json`, `retry.json`

### 4. Modifiche a `routers/chat.py`

L'endpoint `POST /api/v1/chat/stream` usa una `asyncio.Queue` per bridging tra l'async generator e la TTS pipeline concorrente:

```
event_stream():
  audio_queue = asyncio.Queue()
  sentence_buffer = SentenceBuffer()
  tts_pipeline = TtsPipeline(voice, audio_queue)

  # Task concorrente: ascolta audio_queue e yielda eventi SSE
  async def audio_drainer():
      while True:
          chunk = await audio_queue.get()
          if chunk is None: break
          yield chunk
          if chunk["type"] == "done": break

  # Task principale: legge LLM + sentence buffer
  merge_iter = _merge_iterators(
      _token_stream(llm_provider, prompt, history, message),
      audio_drainer()
  )

  async for event in merge_iter:
      yield event
      if event["type"] == "done": break
```

Il `merge_iter` intercala token e audio nell'ordine in cui arrivano, senza bloccare l'uno sull'altro. Ogni frase completa genera audio in parallelo tramite `asyncio.create_task()`. I chunk audio arrivano via `audio_queue` e vengono emessi come eventi `"audio"` tra un token e l'altro.

### 5. Modifiche a `routers/tts.py`

Nessuna modifica. L'endpoint `/api/v1/tts` resta per compatibilità (usato dal metodo `speak()` del web component). La nuova pipeline usa una funzione interna che fa la stessa cosa ma streammata.

## Frontend

### Web component (SpeakingAvatar.svelte / AvatarChat.svelte)

Nessuna modifica. Il web component resta solo l'avatar 3D con metodo `speak(text)`.

### Moodle plugin

Il codice JS inline in `moodle-config.php` viene esteso per gestire gli eventi audio:

```
SSE reader (esistente, già processa "token" e "done")
  │
  ├─ event "token"  → append DOM (esistente)
  ├─ event "audio"  → decode base64 → audio chunk → play queue
  ├─ event "done"   → cleanup (esistente)
  └─ play queue:
       accumulate chunk in AudioBuffer
       programma play con AudioContext.createBufferSource()
       start(when) scheduling preciso
```

Implementazione play queue:

```javascript
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
let nextPlayTime = audioCtx.currentTime;

async function onAudioChunk(base64data, duration) {
  const resp = await fetch(`data:audio/mpeg;base64,${base64data}`);
  const arrayBuffer = await resp.arrayBuffer();
  const audioBuffer = await audioCtx.decodeAudioData(arrayBuffer);
  const source = audioCtx.createBufferSource();
  source.buffer = audioBuffer;
  source.connect(audioCtx.destination);
  source.start(nextPlayTime);
  nextPlayTime += duration;
}
```

## Testing

1. **Unit test SentenceBuffer**: push token, verifica boundary a varie soglie e backpressure
2. **Unit test AudioCache**: hit/miss/eviction L1, caricamento L2 all'avvio
3. **Integration test pipeline**: mocked LLM stream + real Edge TTS → verifica eventi audio in output
4. **End-to-end manual**: Moodle chat → verifica audio progressivo mentre testo continua ad arrivare

## Non-in-scope

- Phoneme-level viseme mapping (sostituisce random_viseme con mapping fonema → morph target)
- WebSocket al posto di SSE (troppo complesso per il beneficio)
- Persistenza sessioni su database (in-memory va bene)
- Gestione code audio parallele per più utenti (coda globale FIFO)

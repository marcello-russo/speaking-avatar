<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import AvatarChat from '$lib/components/chat/AvatarChat.svelte';
  import AvatarWrapper from '$lib/components/chat/AvatarWrapper.svelte';
  import { settings } from '$lib/stores';

  export let ttsApi: string = 'http://localhost:8000/api/v1';
  export let sttApi: string = 'http://localhost:8000/api/v1/stt';
  export let llmApi: string = 'http://localhost:8000/api/v1/chat/stream';
  export let voice: string = 'it-IT-ElsaNeural';
  export let avatar: string = 'The Coach';
  export let element: HTMLElement | null = null;
  export let context: string = '';
  export let mode: string = 'minimal';
  export let minimized: boolean = false;

  let currentMessage = '';
  let speaking = false;
  let _speakResolve: ((value: void | PromiseLike<void>) => void) | null = null;
  let _speakReject: ((reason?: any) => void) | null = null;
  let _lastSpokenLen = 0;

  function emit(type: string, detail: any) {
    if (element) {
      element.dispatchEvent(new CustomEvent(type, { detail, bubbles: false }));
    }
  }

  onMount(() => {
    (settings as any).set({ selectedAvatarId: avatar });
    (window as any).__SPEAKING_AVATAR_API__ = ttsApi.replace('/api/v1', '');
    // Set static base URL for GLB files (CDN or dev server)
    (window as any).__AVATAR_STATIC_BASE__ =
      (window as any).__AVATAR_STATIC_BASE__ || '';
    window.addEventListener('avatar-viseme', _onViseme);
  });

  onDestroy(() => {
    window.removeEventListener('avatar-viseme', _onViseme);
  });

  function _onViseme(e: Event) {
    const ce = e as CustomEvent;
    emit('viseme', ce.detail);
  }

  // ── Public API (exported functions) ──

  export async function speak(text: string): Promise<void> {
    // Resolve any pending speak promise
    if (_speakResolve) { _speakResolve(); _speakResolve = null; _speakReject = null; }
    return new Promise((resolve, reject) => {
      currentMessage = text;
      speaking = true;
      _speakResolve = resolve;
      _speakReject = reject;
      emit('speechstart', { text });
    });
  }

  export async function listen(audio: Blob | File): Promise<string> {
    const form = new FormData();
    form.append('audio', audio);
    const res = await fetch(sttApi, { method: 'POST', body: form });
    if (!res.ok) {
      emit('error', { error: 'STT failed: ' + res.status, source: 'stt' });
      throw new Error('STT failed: ' + res.status);
    }
    const data = await res.json();
    return data.text;
  }

  export async function ask(message: string): Promise<string> {
    const res = await fetch(llmApi, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, context }),
    });
    if (!res.ok) {
      emit('error', { error: 'LLM failed', source: 'llm' });
      throw new Error('LLM failed: ' + res.status);
    }

    _lastSpokenLen = 0;
    let full = '';
    const reader = res.body?.getReader();
    const decoder = new TextDecoder();

    if (reader) {
      let buf = '';
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        const lines = buf.split('\n');
        buf = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = line.slice(6);
            if (data === '[DONE]') continue;
            try {
              const ev = JSON.parse(data);
              if (ev.token) {
                full += ev.token;
                currentMessage = full;
                // Start speaking after first complete sentence or 40 chars
                if (!speaking && (full.includes('.') || full.includes('!') || full.includes('?') || full.length > 40)) {
                  speakEarly(full);
                }
              }
              if (ev.done) break;
            } catch { /* skip parse errors */ }
          }
        }
      }
    }

    // If we haven't started speaking yet, speak the whole thing
    if (!speaking && full) {
      await speak(full);
    }

    return full;
  }

  function speakEarly(text: string) {
    _lastSpokenLen = text.length;
    speak(text);
  }

  export function configure(opts: Record<string, string>): void {
    if (opts.ttsApi) { ttsApi = opts.ttsApi; (window as any).__SPEAKING_AVATAR_API__ = ttsApi.replace('/api/v1', ''); }
    if (opts.sttApi) sttApi = opts.sttApi;
    if (opts.llmApi) llmApi = opts.llmApi;
    if (opts.voice) voice = opts.voice;
    if (opts.avatar) { avatar = opts.avatar; (settings as any).set({ selectedAvatarId: avatar }); }
    if (opts.mode) mode = opts.mode;
    if (opts.minimized !== undefined) minimized = opts.minimized === 'true';
  }

  // ── Handle AvatarChat events ──
  function handleSpeechEnd() {
    speaking = false;
    emit('speechend', { text: currentMessage });
    if (_speakResolve) {
      _speakResolve();
      _speakResolve = null;
      _speakReject = null;
    }
  }
</script>

<div class="sa-root" class:sa-minimal={mode === 'minimal'}>
  {#if mode === 'widget'}
    <AvatarWrapper bind:minimized>
      {#key avatar}
        <AvatarChat
          {currentMessage}
          {speaking}
          useClassroom={false}
          on:speechend={handleSpeechEnd}
        />
      {/key}
    </AvatarWrapper>
  {:else}
    {#key avatar}
      <AvatarChat
        {currentMessage}
        {speaking}
        useClassroom={false}
        on:speechend={handleSpeechEnd}
      />
    {/key}
  {/if}
</div>

<style>
  .sa-root { width: 100%; height: 100%; position: relative; }
  .sa-root.sa-minimal { width: 100%; height: 100%; }
  .sa-root :global(canvas) { width: 100% !important; height: 100% !important; }
</style>

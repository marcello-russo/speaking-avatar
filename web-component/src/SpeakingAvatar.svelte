<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import AvatarChat from '$lib/components/chat/AvatarChat.svelte';
  import { settings } from '$lib/stores';

  export let ttsApi: string = 'http://localhost:8000/api/v1';
  export let sttApi: string = 'http://localhost:8000/api/v1/stt';
  export let llmApi: string = 'http://localhost:8000/api/v1/chat';
  export let voice: string = 'it-IT-ElsaNeural';
  export let avatar: string = 'The Coach';
  export let element: HTMLElement | null = null;

  let currentMessage = '';
  let speaking = false;
  let _speakResolve: ((value: void | PromiseLike<void>) => void) | null = null;
  let _speakReject: ((reason?: any) => void) | null = null;

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
      body: JSON.stringify({ message }),
    });
    if (!res.ok) {
      emit('error', { error: 'LLM failed', source: 'llm' });
      throw new Error('LLM failed: ' + res.status);
    }
    const data = await res.json();
    await speak(data.reply);
    return data.reply;
  }

  export function configure(opts: Record<string, string>): void {
    if (opts.ttsApi) { ttsApi = opts.ttsApi; (window as any).__SPEAKING_AVATAR_API__ = ttsApi.replace('/api/v1', ''); }
    if (opts.sttApi) sttApi = opts.sttApi;
    if (opts.llmApi) llmApi = opts.llmApi;
    if (opts.voice) voice = opts.voice;
    if (opts.avatar) { avatar = opts.avatar; (settings as any).set({ selectedAvatarId: avatar }); }
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

<div class="sa-root">
  {#key avatar}
    <AvatarChat
      {currentMessage}
      {speaking}
      useClassroom={false}
      on:speechend={handleSpeechEnd}
    />
  {/key}
</div>

<style>
  .sa-root { width: 100%; height: 100%; position: relative; }
  .sa-root :global(canvas) { width: 100% !important; height: 100% !important; }
</style>

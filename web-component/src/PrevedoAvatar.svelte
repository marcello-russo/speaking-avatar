<svelte:options customElement="prevedo-avatar" />

<script lang="ts">
  import { onMount } from 'svelte';
  import AvatarChat from '$lib/components/chat/AvatarChat.svelte';
  import { settings } from '$lib/stores';

  // Props exposed as HTML attributes
  export let course: string = '';
  export let theme: 'light' | 'dark' = 'light';
  export let apibase: string = 'http://localhost:8000';

  let messages: { role: string; content: string }[] = [];
  let inputText = '';
  let currentMessage = '';
  let speaking = false;
  let isLoading = false;
  let chatOpen = false;
  let chatContainer: HTMLDivElement;

  onMount(() => {
    document.documentElement.setAttribute('data-theme', theme);
  });

  function addMessage(role: string, content: string) {
    messages = [...messages, { role, content }];
  }

  async function sendMessage() {
    if (!inputText.trim() || isLoading) return;
    const text = inputText;
    inputText = '';
    addMessage('user', text);
    if (!chatOpen) chatOpen = true;
    isLoading = true;

    try {
      const res = await fetch(`${apibase}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, course_context: course }),
      });
      const data = await res.json();
      addMessage('assistant', data.reply);
      currentMessage = data.reply;
      speaking = true;
    } catch {
      addMessage('assistant', 'Errore di connessione.');
    }
    isLoading = false;
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
  }

  $: if (chatContainer) chatContainer.scrollTop = chatContainer.scrollHeight;
</script>

<div class="prevedo-root" class:dark={theme === 'dark'}>
  <!-- Avatar full-width -->
  <div class="avatar-section">
    <AvatarChat
      {currentMessage}
      {speaking}
      useClassroom={false}
      on:speechend={() => { speaking = false; }}
    />
  </div>

  <!-- Chat bubble -->
  {#if chatOpen}
    <div class="chat-panel">
      <div class="messages" bind:this={chatContainer}>
        {#each messages as msg}
          <div class="msg {msg.role}">{msg.content}</div>
        {/each}
        {#if isLoading}<div class="msg assistant typing">...</div>{/if}
      </div>
      <div class="input-row">
        <input type="text" bind:value={inputText} on:keydown={handleKeydown}
          placeholder="Scrivi..." disabled={isLoading} />
        <button on:click={sendMessage} disabled={!inputText.trim() || isLoading}>Invia</button>
      </div>
    </div>
  {/if}

  <!-- FAB to toggle chat -->
  <button class="fab" on:click={() => { chatOpen = !chatOpen; }}>
    {chatOpen ? '✕' : '💬'}
  </button>
</div>

<style>
  .prevedo-root {
    position: fixed; inset: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  }
  .prevedo-root.dark { background: #0a0a14; color: #e2e8f0; }
  .prevedo-root:not(.dark) { background: #f8f9fc; color: #1e293b; }

  .avatar-section { width: 100%; height: 100%; }
  .avatar-section :global(canvas) { width: 100% !important; height: 100% !important; }

  .chat-panel {
    position: absolute; bottom: 80px; right: 20px;
    width: 360px; height: 460px;
    background: var(--chat-bg, white);
    border: 1px solid var(--chat-border, #e2e8f0);
    border-radius: 16px;
    display: flex; flex-direction: column;
    box-shadow: 0 8px 32px rgba(0,0,0,0.15);
    overflow: hidden;
  }
  .dark .chat-panel { --chat-bg: #1a1a2e; --chat-border: #2a2a4a; }

  .messages { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; gap: 8px; font-size: 14px; }
  .msg { padding: 8px 12px; border-radius: 12px; max-width: 85%; line-height: 1.4; }
  .msg.user { align-self: flex-end; background: #6366f1; color: white; border-bottom-right-radius: 3px; }
  .msg.assistant { align-self: flex-start; background: #f1f3f8; border: 1px solid #e2e8f0; border-bottom-left-radius: 3px; }
  .dark .msg.assistant { background: #1a1a33; border-color: #2a2a4a; }
  .msg.typing { color: #6366f1; font-size: 18px; }

  .input-row { display: flex; gap: 8px; padding: 12px; border-top: 1px solid var(--chat-border, #e2e8f0); }
  .input-row input { flex: 1; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 13px; outline: none; }
  .dark .input-row input { background: #12121e; border-color: #2a2a4a; color: #e2e8f0; }
  .input-row input:focus { border-color: #6366f1; }
  .input-row button { padding: 8px 16px; background: #6366f1; color: white; border: none; border-radius: 8px; font-size: 13px; cursor: pointer; }
  .input-row button:disabled { opacity: 0.4; }

  .fab {
    position: absolute; bottom: 20px; right: 20px;
    width: 56px; height: 56px; border-radius: 50%;
    background: #6366f1; color: white; border: none;
    font-size: 24px; cursor: pointer;
    box-shadow: 0 4px 16px rgba(99,102,241,0.4);
    z-index: 10;
  }
</style>

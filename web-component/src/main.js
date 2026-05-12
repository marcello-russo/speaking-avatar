import { mount } from 'svelte';
import SpeakingAvatar from './SpeakingAvatar.svelte';

class SpeakingAvatarElement extends HTMLElement {
  connectedCallback() {
    const props = {
      ttsApi: this.getAttribute('tts-api') || this.getAttribute('ttsapi') || 'http://localhost:8000/api/v1',
      sttApi: this.getAttribute('stt-api') || this.getAttribute('sttapi') || 'http://localhost:8000/api/v1/stt',
      llmApi: this.getAttribute('llm-api') || this.getAttribute('llmapi') || 'http://localhost:8000/api/v1/chat',
      voice: this.getAttribute('voice') || 'it-IT-ElsaNeural',
      avatar: this.getAttribute('avatar') || 'The Coach',
      element: this,
    };

    this.style.display = 'block';
    this.style.width = '100%';
    this.style.height = '100%';

    const inst = mount(SpeakingAvatar, { target: this, props });

    this.speak = inst.speak;
    this.listen = inst.listen;
    this.ask = inst.ask;
    this.configure = inst.configure;
  }
}

customElements.define('speaking-avatar', SpeakingAvatarElement);
export default SpeakingAvatarElement;

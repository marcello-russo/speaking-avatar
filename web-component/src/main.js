import { mount } from 'svelte';
import SpeakingAvatar from './SpeakingAvatar.svelte';

class SpeakingAvatarElement extends HTMLElement {
  connectedCallback() {
    const context = this.getAttribute('context') || '';
    const theme = this.getAttribute('theme') || 'light';
    const accent = this.getAttribute('accent') || '#6366f1';
    const apiurl = this.getAttribute('apiurl') || 'http://localhost:8000/api/v1';
    const avatar = this.getAttribute('avatar') || 'The Coach';
    const title = this.getAttribute('title') || 'AI Tutor';
    const fab = this.getAttribute('fab') || 'true';

    this.style.display = 'block';
    this.style.width = '100vw';
    this.style.height = '100vh';

    mount(SpeakingAvatar, {
      target: this,
      props: { context, theme, accent, apiurl, avatar, title, fab },
    });
  }
}

customElements.define('speaking-avatar', SpeakingAvatarElement);

export default SpeakingAvatarElement;

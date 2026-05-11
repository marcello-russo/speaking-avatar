import { writable } from 'svelte/store';

export const settings = writable({
  selectedAvatarId: 'The Coach',
});

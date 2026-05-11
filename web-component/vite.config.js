import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  resolve: {
    alias: {
      $lib: path.resolve('./src/lib'),
    },
  },
  build: {
    lib: {
      entry: path.resolve('./src/main.js'),
      name: 'SpeakingAvatar',
      formats: ['es', 'umd'],
      fileName: (format) => `speaking-avatar.${format}.js`,
    },
    rollupOptions: {
      output: {
        globals: {},
      },
    },
  },
})

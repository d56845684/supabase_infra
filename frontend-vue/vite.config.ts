import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import checker from 'vite-plugin-checker';

export default defineConfig({
  plugins: [vue(), vueJsx(), checker({ typescript: true })],
  resolve: {
    alias: {
      '@': '/src',
      '#': '/src/types'
    }
  }
});

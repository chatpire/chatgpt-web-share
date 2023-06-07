import { fileURLToPath, URL } from 'node:url';

import presetUno from '@unocss/preset-uno';
import UnoCSS from '@unocss/vite';
import vue from '@vitejs/plugin-vue';
import { join } from 'path';
import { transformerDirectives } from 'unocss';
import { NaiveUiResolver } from 'unplugin-vue-components/resolvers';
import Components from 'unplugin-vue-components/vite';
import { defineConfig } from 'vite';
import svgLoader from 'vite-svg-loader';

// import { IconComponentResolver } from './utils/icon-component-resolver';

// https://vitejs.dev/config/
export default defineConfig({
  base: process.env.VITE_BASE || '/',
  plugins: [
    vue(),
    svgLoader(),
    UnoCSS({
      presets: [presetUno()],
      transformers: [transformerDirectives()],
    }),
    Components({
      resolvers: [
        NaiveUiResolver(),
        // IconComponentResolver({ pkgs: ['@vicons/ionicons4', '@vicons/ionicons5', '@vicons/material'], prefix: 'X' }),
      ],
    }),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('../src', import.meta.url)),
    },
  },
  define: {
    'import.meta.env.PACKAGE_VERSION': JSON.stringify(process.env.npm_package_version),
    'import.meta.env.VITE_ENABLE_SENTRY': process.env.VITE_ENABLE_SENTRY || '\'no\'',
    'import.meta.env.VITE_ROUTER_BASE': process.env.VITE_ROUTER_BASE || '\'/\'',
    'import.meta.env.VITE_API_BASE_URL': process.env.VITE_API_BASE_URL || '\'/api/\'',
  },
});

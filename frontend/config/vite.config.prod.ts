import { mergeConfig } from 'vite';

import baseConfig from './vite.config.base';

export default mergeConfig(
  {
    mode: 'production',
    plugins: [],
    build: {
      sourcemap: process.env.VITE_DISABLE_SOURCEMAP !== 'yes',
      rollupOptions: {
        output: {
          manualChunks: {
            naive_ui: ['naive-ui'],
            vue: ['vue', 'vue-router', 'pinia', 'vue-i18n'],
          },
        },
      },
      chunkSizeWarningLimit: 2000,
    },
  },
  baseConfig
);

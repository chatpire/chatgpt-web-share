import { mergeConfig } from "vite";
import baseConfig from "./vite.config.base";

export default mergeConfig(
  {
    mode: "production",
    plugins: [],
    build: {
      rollupOptions: {
        output: {
          manualChunks: {
            naive_ui: ["naive-ui"],
            vue: ["vue", "vue-router", "pinia", "vue-i18n"],
          },
        },
      },
      chunkSizeWarningLimit: 2000,
    },
    define: {
      "import.meta.env.VITE_API_WEBSOCKET_PROTOCOL": "'wss'",
    },
  },
  baseConfig
);

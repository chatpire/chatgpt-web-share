import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import UnoCSS from "@unocss/vite";
import presetUno from "@unocss/preset-uno";
import { join } from "path";
import Components from "unplugin-vue-components/vite";
import { NaiveUiResolver } from "unplugin-vue-components/resolvers";
import { transformerDirectives } from "unocss";
import { fileURLToPath, URL } from "node:url";

// https://vitejs.dev/config/
export default defineConfig({
  base: "./",
  plugins: [
    vue(),
    UnoCSS({
      presets: [
        /* no presets by default */
        presetUno(),
      ],
      /* options */
      transformers: [transformerDirectives()],
    }),
    Components({
      resolvers: [NaiveUiResolver()],
    }),
  ],
  define: {
    "process.env": {},
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("../src", import.meta.url)),
    },
  },
});

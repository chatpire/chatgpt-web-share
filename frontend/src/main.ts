import Vue from "vue";
import pinia from "./store";
import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";
import "uno.css";
import "@/api/interceptor";
import router from "./router";

import { i18n } from "./i18n";
import "highlight.js/styles/atom-one-dark.css";
import "highlight.js/lib/common";

import "katex/dist/katex.css";

const app = createApp(App);

app.use(router);
app.use(pinia);
app.use(i18n);
// app.use(hljs.vuePlugin);

app.mount("#app");

declare global {
  interface Window {
    $message: any;
  }
}

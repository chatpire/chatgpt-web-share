import Vue from "vue";
import pinia from "./store";
import { createApp } from "vue";
import "./style.css";
import App from "./App.vue";
import "uno.css";
import { i18n } from "./i18n";
import "@/api/interceptor";
import router from "./router";

import "highlight.js/styles/atom-one-dark.css";
import "highlight.js/lib/common";

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

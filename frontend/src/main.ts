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

import * as Sentry from "@sentry/vue";
import { BrowserTracing } from "@sentry/tracing";

const app = createApp(App);

if (import.meta.env.VITE_DISABLE_SENTRY !== "yes") {
  Sentry.init({
    app,
    dsn: "https://025ea375ad134baba1f7b11d68d24fa5@o4504870115999745.ingest.sentry.io/4504885986263040",
    integrations: [
      new BrowserTracing({
        routingInstrumentation: Sentry.vueRouterInstrumentation(router),
        // tracePropagationTargets: ["localhost", "my-site-url.com", /^\//],
      }),
    ],
    tracesSampleRate: 1.0,
  });
}

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

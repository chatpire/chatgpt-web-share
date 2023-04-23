import './style.css';
// eslint-disable-next-line import/no-unresolved
import 'uno.css';
import '@/api/interceptor';
import 'highlight.js/styles/atom-one-dark.css';
import 'highlight.js/lib/common';
import 'katex/dist/katex.css';

import { createApp } from 'vue';

import App from './App.vue';
import { i18n } from './i18n';
import router from './router';
import pinia from './store';

// import * as Sentry from "@sentry/vue";
// import { BrowserTracing } from "@sentry/tracing";

const app = createApp(App);

// if (import.meta.env.VITE_ENABLE_SENTRY === "yes") {
//   Sentry.init({
//     app,
//     dsn: import.meta.env.VITE_SENTRY_DSN || "",
//     integrations: [
//       new BrowserTracing({
//         routingInstrumentation: Sentry.vueRouterInstrumentation(router),
//         // tracePropagationTargets: ["localhost", "my-site-url.com", /^\//],
//       }),
//     ],
//     tracesSampleRate: 1.0,
//     ignoreErrors: ["AxiosError", "errors."]
//   });
// }

app.use(router);
app.use(pinia);
app.use(i18n);
// app.use(hljs.vuePlugin);

app.mount('#app');

declare global {
  interface Window {
    $message: any;
  }
}

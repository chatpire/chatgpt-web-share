import './style.css';
// eslint-disable-next-line import/no-unresolved
import 'uno.css';
import '@/api/interceptor';
import 'katex/dist/katex.css';

import {
  NButton,
  NCheckbox,
  NCheckboxGroup,
  NDatePicker,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NPopover,
  NSelect,
  NSpace,
  NSwitch,
  NTimePicker,
} from 'naive-ui';
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

// app.component('NForm', NForm);
// app.component('NFormItem', NFormItem);
// app.component('NInput', NInput);
// app.component('NInputNumber', NInputNumber);
// app.component('NSwitch', NSwitch);

// 注册部分naive-ui组件，以供vue-form使用
const naiveFormComponents = [
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NSwitch,
  NButton,
  NSelect,
  NPopover,
  NCheckbox,
  NCheckboxGroup,
  NSpace,
  NDatePicker,
  NTimePicker,
];
naiveFormComponents.forEach((component) => {
  app.component(`N${component.name}`, component);
});

app.mount('#app');

declare global {
  interface Window {
    $message: any;
  }
}

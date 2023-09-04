import './style.css';
import 'uno.css';
import '@/api/interceptor';
import 'katex/dist/katex.css';

import { NButton, NCheckbox, NCheckboxGroup, NDatePicker, NForm, NFormItem, NInput, NInputNumber, NPopover, NSelect, NSpace, NSwitch, NTimePicker } from 'naive-ui';
import { createApp } from 'vue';

import App from './App.vue';
import { i18n } from './i18n';
import { createRouter, createWebHistory } from 'vue-router'; // Import Vue Router functions
import pinia from './store';
import routerConfig from './router'; // Import your router configuration

const app = createApp(App);

const vueRouter = createRouter({
  history: createWebHistory(),
  routes: routerConfig, // Use your router configuration here
});

app.use(vueRouter);

app.use(pinia);
app.use(i18n);
// app.use(hljs.vuePlugin);

// app.component('NForm', NForm);
// app.component('NFormItem', NFormItem);
// app.component('NInput', NInput);
// app.component('NInputNumber', NInputNumber);
// app.component('NSwitch', NSwitch);

// 注册部分naive-ui组件，以供vue-form使用
const naiveFormComponents = [NForm, NFormItem, NInput, NInputNumber, NSwitch, NButton, NSelect, NPopover, NCheckbox, NCheckboxGroup, NSpace, NDatePicker, NTimePicker];
naiveFormComponents.forEach((component) => {
  app.component(`N${component.name}`, component);
});

app.mount('#app');

declare global {
  interface Window {
    $message: any;
  }
}

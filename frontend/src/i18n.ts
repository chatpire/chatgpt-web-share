import { useStorage } from '@vueuse/core';
import { WritableComputedRef } from 'vue';
import { createI18n, type I18n, type Locale } from 'vue-i18n';

import EN from './locales/en-US.json';
import ZH from './locales/zh-CN.json';

let i18n: I18n;

const init = () => {
  i18n = createI18n({
    legacy: false,
    locale: useStorage('language', 'zh-CN').value,
    messages: {
      'en-US': {
        ...EN,
      },
      'zh-CN': {
        ...ZH,
      },
    },
  });
};

const setLocale = (locale: Locale): void => {
  (i18n.global.locale as WritableComputedRef<string>).value = locale;
};

init();

export { i18n, setLocale };

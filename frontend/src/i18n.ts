import { createI18n, type I18n, type Locale } from "vue-i18n";
import EN from "./locales/en.json";
import ZH from "./locales/zh.json";

let i18n: I18n;

const init = () => {
  i18n = createI18n({
    legacy: false,
    locale: "zh",
    messages: {
      en: {
        ...EN
      },
      zh: {
        ...ZH
      },
    },
  });
};

const setLocale = (locale: Locale): void => {
  i18n.global.locale = locale;
};

init();

export { i18n, setLocale };
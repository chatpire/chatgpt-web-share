import { defineStore } from "pinia";
import { AppState } from "../types";
import { useOsTheme } from "naive-ui";
const osThemeRef = useOsTheme();
import { useStorage } from "@vueuse/core";
import { setLocale } from "@/i18n";

const useAppStore = defineStore("app", {
  state: (): AppState => ({
    theme: useStorage("theme", osThemeRef.value),
    language: useStorage("language", "zh"),
  }),
  getters: {},
  actions: {
    setTheme(theme: string | null) {
      this.theme = theme;
    },
    // 切换主题
    toggleTheme() {
      this.theme = this.theme === "dark" ? "light" : "dark";
    },
    setLanguage(lang: string) {
      this.language = lang;
      setLocale(lang);
    },
  },
});

export default useAppStore;

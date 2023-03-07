import { defineStore } from "pinia";
import { AppState } from "../types";
import { useOsTheme } from 'naive-ui';
const osThemeRef = useOsTheme();

const useAppStore = defineStore("app", {
  state: (): AppState => ({
    theme: osThemeRef.value
  }),
  getters: {
  },
  actions: {
    setTheme(theme: string | null) {
      this.theme = theme;
    },
    // 切换主题
    toggleTheme() {
      console.log("toggleTheme");
      this.theme = this.theme === "dark" ? null : "dark";
    }
  },
});

export default useAppStore;

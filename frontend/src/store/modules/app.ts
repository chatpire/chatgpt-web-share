import { useOsTheme } from 'naive-ui';
import { defineStore } from 'pinia';

import { AppState, Preference } from '../types';
const osThemeRef = useOsTheme();
import { useStorage } from '@vueuse/core';

import { setLocale } from '@/i18n';
import { ChatSourceTypes } from '@/types/schema';
import { themeRef } from '@/utils/tips';

const useAppStore = defineStore('app', {
  state: (): AppState => ({
    theme: useStorage('theme', osThemeRef.value),
    language: useStorage('language', 'zh-CN'),
    preference: useStorage<Preference>('preference', {
      sendKey: 'Enter',
      renderUserMessageInMd: false,
      codeAutoWrap: false,
      widerConversationPage: true,
    }),
    lastSelectedSource: useStorage<ChatSourceTypes>('lastSelectedSource', null),
    lastSelectedModel: useStorage<string | null>('lastSelectedModel', null),
  }),
  getters: {},
  actions: {
    // 切换主题
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark';
      themeRef.value = this.theme;
    },
    setLanguage(lang: string) {
      this.language = lang;
      setLocale(lang);
    },
  },
});

export default useAppStore;

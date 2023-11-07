import { useStorage } from '@vueuse/core';
import { defineStore } from 'pinia';

import { getUserMeApi, loginApi, LoginData, logoutApi } from '@/api/user';
import { UserRead } from '@/types/schema';
import { clearCookie } from '@/utils/auth';

import { UserState } from '../types';

const useUserStore = defineStore('user', {
  state: (): UserState => ({
    user: null,
    savedLoginForm: useStorage('savedLoginForm', {
      rememberPassword: false,
      savedUsername: undefined,
      savedPassword: undefined,
    }),
  }),
  getters: {
    userInfo(): UserRead | null {
      return this.user;
    },
  },

  actions: {
    // Set user's information
    setInfo(user: UserRead) {
      this.$patch({ user });
    },

    setSavedLoginInfo(username: string, password: string) {
      this.savedLoginForm.savedUsername = username;
      this.savedLoginForm.savedPassword = password;
    },

    // Reset user's information
    resetInfo() {
      this.$reset();
    },

    // Get user's information
    async fetchUserInfo() {
      const result = (await getUserMeApi()).data;
      this.setInfo(result);
    },

    // Login
    async login(loginForm: LoginData) {
      try {
        await loginApi(loginForm);
        // setToken(res.data.token);
      } catch (err) {
        clearCookie();
        throw err;
      }
    },

    // Logout
    async logout() {
      try {
        await logoutApi();
      } finally {
        this.resetInfo();
        clearCookie();
      }
    },
  },
});

export default useUserStore;

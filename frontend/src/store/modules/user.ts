import { defineStore } from 'pinia';

import { getUserMeApi, loginApi, LoginData, logoutApi } from '@/api/user';
import { UserRead } from '@/types/schema';
import { clearCookie } from '@/utils/auth';

import { UserState } from '../types';

const useUserStore = defineStore('user', {
  state: (): UserState => ({
    user: null,
    savedUsername: null,
    savedPassword: null,
  }),
  getters: {
    userInfo(state: UserState): UserRead | null {
      return state.user;
    },
  },

  actions: {
    // Set user's information
    setInfo(user: UserRead) {
      this.$patch({ user });
    },

    setSavedLoginInfo(username: string, password: string) {
      this.$patch({ savedUsername: username, savedPassword: password });
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

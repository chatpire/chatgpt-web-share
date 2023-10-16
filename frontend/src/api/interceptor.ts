import type { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import axios from 'axios';

import { i18n } from '@/i18n';
import router from '@/router';
import { useUserStore } from '@/store';
import { Dialog, Message } from '@/utils/tips';

// import { isLogin } from '@/utils/auth';
import ApiUrl from './url';
const t = i18n.global.t as any;

export interface HttpResponse<T = unknown> {
  code: number;
  message: string;
  result: T;
}

axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL;
// axios.defaults.baseURL = "/openai_api/";

axios.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // if (token) {
    //   if (!config.headers) {
    //     config.headers = {};
    //   }
    //   config.headers.Authorization = `Bearer ${token}`;
    // }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * 添加响应拦截器
 * 这里将 { code, message, result } 解构出来，response.data 替换成 result
 */
const successCode = [200, 201, 204];
axios.interceptors.response.use(
  (response: AxiosResponse<HttpResponse>) => {
    const res = response.data;
    if (!successCode.includes(res.code)) {
      console.warn('Error: ', res);
      let msg = `${res.code}`;
      if (res.message) {
        msg += ` ${t(res.message)}`;
      }
      if (res.result) {
        msg += `: ${t(res.result)}`;
      }
      Message.error(msg, { duration: 3 * 1000 });
      if (
        [10401].includes(res.code) &&
        !([ApiUrl.Login, ApiUrl.Logout] as Array<string>).includes(response.config.url || '')
      ) {
        Dialog.error({
          title: t('errors.loginExpired') as string,
          content: t('tips.loginExpired'),
          positiveText: t('commons.confirm'),
          negativeText: t('commons.stayInCurrentPage'),
          onPositiveClick() {
            const userStore = useUserStore();
            userStore.logout().then(() => {
              router.push({ name: 'login' });
            });
            window.location.reload();
          },
        });
      }
      return Promise.reject(res);
    }
    (response.data as any) = res.result;
    return response;
  },
  (error) => {
    Message.error((error.msg && t(error.msg)) || 'Request Error', {
      duration: 5 * 1000,
    });
    console.error('Request Error', error);
    return Promise.reject(error);
  }
);

import axios from "axios";
import type { InternalAxiosRequestConfig, AxiosResponse } from "axios";
import { useUserStore } from "@/store";
import { Message, Dialog } from "@/utils/tips";
// import { isLogin } from '@/utils/auth';
import ApiUrl from "./url";
import router from "@/router";

import { i18n } from "@/i18n";
const t = i18n.global.t as any;

export interface HttpResponse<T = unknown> {
  code: number;
  message: string;
  result: T;
}

// if (import.meta.env.VITE_API_BASE_URL) {
//   axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL;
// }
axios.defaults.baseURL = "/api/";

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
    if ([201, 204].includes(response.status)) {
      return response;
    }
    const res = response.data;
    if (!successCode.includes(res.code)) {
      console.log("Error: ", res);
      let msg = `${res.code}`;
      if (res.message) {
        msg += `: ${res.message}`;
      }
      Message.error(msg, {
        duration: 5 * 1000,
      });
      if (
        [401].includes(res.code) &&
        !([ApiUrl.Login, ApiUrl.Logout] as Array<string>).includes(
          response.config.url || ""
        )
      ) {
        Dialog.error({
          title: t("errors.loginExpired") as string,
          content: t("tips.loginExpired"),
          positiveText: t("commons.confirm"),
          negativeText: t("commons.stayInCurrentPage"),
          onPositiveClick() {
            const userStore = useUserStore();
            userStore.logout().then(() => {
              router.push({ name: "login" });
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
    Message.error((error.msg && t(error.msg)) || `Request Error`, {
      duration: 5 * 1000,
    });
    console.error("Request Error", error);
    return Promise.reject(error);
  }
);

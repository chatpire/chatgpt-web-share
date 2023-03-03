import { ref, computed } from "vue";

import {
  createDiscreteApi,
  ConfigProviderProps,
  darkTheme,
  lightTheme,
} from "naive-ui";

const themeRef = ref<"light" | "dark">("light");
const configProviderPropsRef = computed<ConfigProviderProps>(() => ({
  theme: themeRef.value === "light" ? lightTheme : darkTheme,
}));

const { message, notification, dialog, loadingBar } = createDiscreteApi(
  ["message", "dialog", "notification", "loadingBar"],
  { configProviderProps: configProviderPropsRef }
);

export {
  message as Message,
  notification as Notification,
  dialog as Dialog,
  loadingBar as LoadingBar,
  themeRef,
};

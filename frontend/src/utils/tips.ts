import { useStorage } from '@vueuse/core';
import { ConfigProviderProps, createDiscreteApi, darkTheme, lightTheme } from 'naive-ui';
import { computed, ref } from 'vue';

const themeRef = ref<'light' | 'dark'>(useStorage('theme', 'light').value as any);
const configProviderPropsRef = computed<ConfigProviderProps>(() => ({
  theme: themeRef.value === 'light' ? lightTheme : darkTheme,
}));

const { message, notification, dialog, loadingBar } = createDiscreteApi(
  ['message', 'dialog', 'notification', 'loadingBar'],
  {
    configProviderProps: configProviderPropsRef,
  }
);

export { dialog as Dialog, loadingBar as LoadingBar, message as Message, notification as Notification, themeRef };

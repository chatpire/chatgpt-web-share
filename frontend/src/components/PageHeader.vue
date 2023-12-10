<template>
  <n-layout-header bordered style="height: var(--header-height)" class="px-3 flex flex-col justify-center">
    <n-page-header>
      <template #title>
        <n-space :align="'center'">
          <div class="lt-sm:hidden">
            <a href="/" style="text-decoration: none; color: inherit">
              <span class="lt-md:hidden">{{ $t('commons.siteTitleFull') }}</span>
              <span class="md:hidden">{{ $t('commons.siteTitle') }}</span>
            </a>
          </div>
          <div class="hidden sm:block">
            <a class="h-full inline-block flex" href="https://github.com/chatpire/chatgpt-web-share" target="_blank">
              <n-icon :color="appStore.theme == 'dark' ? 'white' : 'black'" :component="LogoGithub" />
            </a>
          </div>
          <n-tag :bordered="false" type="success" size="small" class="hidden sm:inline-flex">
            {{ version }}
          </n-tag>
        </n-space>
      </template>
      <template #avatar>
        <!-- <ChatGPTAvatar color="green" icon-style="default" :size="32" /> -->
        <CWSIcon />
      </template>
      <template #extra>
        <n-space>
          <div class="flex space-x-2 items-center">
            <div v-if="userStore.user" class="inline-block">
              <n-dropdown :options="getOptions()" placement="bottom-start">
                <n-button strong round secondary class="px-2">
                  <n-ellipsis :tooltip="false" style="max-width: 6rem">
                    {{ userStore.user.nickname }}
                  </n-ellipsis>
                  <template #icon>
                    <n-icon><PersonCircleOutline /></n-icon>
                  </template>
                </n-button>
              </n-dropdown>
            </div>
            <div v-else class="text-gray-500 inline-block">
              {{ $t('commons.notLogin') }}
            </div>
            <n-button v-if="userStore.user?.is_superuser" secondary circle @click="jumpToAdminOrConv">
              <n-icon :component="isInAdmin ? ChatFilled : ManageAccountsFilled" />
            </n-button>
            <n-button secondary circle @click="toggleTheme">
              <n-icon :component="themeIcon" />
            </n-button>
          </div>
        </n-space>
      </template>
    </n-page-header>
  </n-layout-header>
</template>

<script setup lang="ts">
import {
  InformationCircleOutline,
  LogoGithub,
  LogOutOutline,
  PersonCircleOutline,
  SettingsSharp,
} from '@vicons/ionicons5';
import { ChatFilled, DarkModeRound, LightModeRound, ManageAccountsFilled, PasswordRound } from '@vicons/material';
import { DropdownOption, NIcon } from 'naive-ui';
import { computed, h } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute } from 'vue-router';

import { updateUserMeApi } from '@/api/user';
import ChatGPTAvatar from '@/components/ChatGPTAvatar.vue';
import CWSIcon from '@/components/icons/CWSIcon.vue';
import router from '@/router';
import { useAppStore, useUserStore } from '@/store';
import { Preference } from '@/store/types';
import { popupResetUserPasswordDialog } from '@/utils/renders';
import { Dialog, Message } from '@/utils/tips';

import PreferenceForm from './PreferenceForm.vue';
import UserProfileCard from './UserProfileCard.vue';

const { t } = useI18n();
const userStore = useUserStore();
const appStore = useAppStore();
const route = useRoute();
const version = 'v' + import.meta.env.PACKAGE_VERSION;

// console.log(route);

const isInAdmin = computed(() => {
  return route.path.startsWith('/admin');
});

const themeIcon = computed(() => {
  if (appStore.theme == 'dark') {
    return DarkModeRound;
  } else {
    return LightModeRound;
  }
});

const toggleTheme = () => {
  appStore.toggleTheme();
};

const getOptions = (): Array<DropdownOption> => {
  const options: Array<DropdownOption> = [
    {
      label: t('commons.userProfile'),
      key: 'profile',
      icon() {
        return h(NIcon, null, {
          default: () => h(InformationCircleOutline),
        });
      },
      props: {
        onClick: () =>
          Dialog.info({
            title: t('commons.userProfile'),
            content: () => h(UserProfileCard, {}, {}),
            positiveText: t('commons.confirm'),
            style: { width: '600px' },
          }),
      },
    },
    {
      label: t('commons.resetPassword'),
      key: 'resetpwd',
      icon() {
        return h(NIcon, null, {
          default: () => h(PasswordRound),
        });
      },
      props: {
        onClick: resetPassword,
      },
    },
    {
      label: t('commons.preferences'),
      key: 'preference',
      icon() {
        return h(NIcon, null, {
          default: () => h(SettingsSharp),
        });
      },
      props: {
        onClick: () => {
          let preference: Preference = {
            ...appStore.preference,
          };
          Dialog.info({
            title: t('commons.preferences'),
            positiveText: t('commons.confirm'),
            negativeText: t('commons.cancel'),
            content: () =>
              h(PreferenceForm, {
                onUpdate: (val: any) => {
                  preference = val;
                },
                value: preference,
              }),
            onPositiveClick() {
              appStore.$patch({
                preference: preference,
              });
              Message.success(t('tips.success'));
            },
          });
        },
      },
    },
    {
      type: 'divider',
      key: 'd1',
    },
    {
      label: t('commons.logout'),
      key: 'logout',
      icon() {
        return h(NIcon, null, {
          default: () => h(LogOutOutline),
        });
      },
      props: {
        onClick: () =>
          Dialog.info({
            title: t('commons.logout'),
            content: t('tips.logoutConfirm'),
            positiveText: t('commons.confirm'),
            negativeText: t('commons.cancel'),
            onPositiveClick: async () => {
              await userStore.logout();
              Message.success(t('commons.logoutSuccess'));
              await router.push({ name: 'login' });
            },
          }),
      },
    },
  ];
  return options;
};

const resetPassword = () => {
  popupResetUserPasswordDialog(
    async (password: string) => {
      await updateUserMeApi({ password });
    },
    () => {
      Message.info(t('tips.resetUserPasswordSuccess'));
    },
    () => {
      Message.error(t('tips.resetUserPasswordFailed'));
    }
  );
};

const jumpToAdminOrConv = async () => {
  if (isInAdmin.value) {
    await router.push({ name: 'conversation' });
  } else {
    await router.push({ name: 'admin' });
  }
};
</script>

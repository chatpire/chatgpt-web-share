<template>
  <n-page-header>
    <template #title>
      <n-space :align="'center'">
        <div>
          <a href="/" style="text-decoration: none; color: inherit">{{ $t("commons.siteTitle") }}</a>
        </div>
        <div class="hidden sm:block">
          <a class="h-full inline-block flex" href="https://github.com/moeakwak/chatgpt-web-share" target="_blank">
            <n-icon :color="appStore.theme == 'dark' ? 'white' : 'black'" :component="LogoGithub" />
          </a>
        </div>
        <n-tag :bordered="false" type="success" size="small" class="hidden sm:inline-flex">
          {{ version }}
        </n-tag>
      </n-space>
    </template>
    <template #avatar>
      <n-avatar :src="chatgptIcon" />
    </template>
    <template #extra>
      <n-space>
        <div class="space-x-2">
          <div v-if="userStore.user" class="inline-block">
            <span class="hidden sm:inline mr-1">Hi, {{ userStore.user.nickname }}</span>
            <n-dropdown :options="getOptions()" placement="bottom-start">
              <n-button circle class="ml-2">
                <n-icon :component="SettingsSharp" />
              </n-button>
            </n-dropdown>
          </div>
          <div v-else class="text-gray-500 inline-block">{{ $t("commons.notLogin") }}</div>
          <n-button v-if="userStore.user?.is_superuser" circle @click="jumpToAdminOrConv">
            <n-icon :component="isInAdmin ? ChatFilled : ManageAccountsFilled" />
          </n-button>
          <n-button circle @click="toggleTheme">
            <n-icon :component="themeIcon" />
          </n-button>
          <n-dropdown :options="languageOptions" placement="bottom-start">
            <n-button circle>
              <n-icon :component="Language" />
            </n-button>
          </n-dropdown>
        </div>
      </n-space>
    </template>
  </n-page-header>
</template>

<script setup lang="ts">
import { useUserStore, useAppStore } from '@/store';
import { SettingsSharp, LogoGithub, Language } from '@vicons/ionicons5';
import { DarkModeRound, LightModeRound, ManageAccountsFilled, ChatFilled } from '@vicons/material';
import { useI18n } from 'vue-i18n';
import { Dialog, Message } from '@/utils/tips';
import router from '@/router';
import { useRoute } from 'vue-router';
import { DropdownOption } from "naive-ui"
import { ref, computed, h } from 'vue';
import UserProfileCard from './UserProfileCard.vue';
import { popupResetUserPasswordDialog } from '@/utils/renders';
import { resetUserPasswordApi } from '@/api/user';
import chatgptIcon from '/chatgpt-icon.svg';
import PreferenceForm from './PreferenceForm.vue';
import { Preference } from '@/types/custom';

const { t } = useI18n();
const userStore = useUserStore();
const appStore = useAppStore();
const route = useRoute();
const version = 'v' + import.meta.env.PACKAGE_VERSION;

console.log(route);

const isInAdmin = computed(() => {
  return route.path.startsWith('/admin');
})

const themeIcon = computed(() => {
  if (appStore.theme == 'dark') {
    return DarkModeRound
  } else {
    return LightModeRound
  }
})

const toggleTheme = () => {
  appStore.toggleTheme();
}

const languageOptions = [
  {
    label: '简体中文',
    key: 'zh-CN',
    props: {
      onClick: () => {
        appStore.setLanguage('zh-CN');
      }
    }
  },
  {
    label: 'English',
    key: 'en-US',
    props: {
      onClick: () => {
        appStore.setLanguage('en-US');
      }
    }
  }
]

const getOptions = (): Array<DropdownOption> => {
  const options: Array<DropdownOption> = [
    {
      label: t("commons.userProfile"),
      key: 'profile',
      props: {
        onClick: () => Dialog.info({
          title: t("commons.userProfile"),
          content: () => h(UserProfileCard, {}, {}),
          positiveText: t("commons.confirm"),
        })
      }
    },
    {
      label: t("commons.resetPassword"),
      key: 'resetpwd',
      props: {
        onClick: resetPassword
      }
    },
    {
      label: t("commons.preferences"),
      key: 'preference',
      props: {
        onClick: () => {
          let preference: Preference = {
            ...appStore.preference
          }
          Dialog.info({
            title: t("commons.preferences"),
            positiveText: t("commons.confirm"),
            negativeText: t("commons.cancel"),
            content: () =>
              h(PreferenceForm, {
                onUpdate: (val: any) => {
                  preference = val;
                },
                value: preference
              }),
            onPositiveClick() {
              appStore.$patch({
                preference: preference
              });
              Message.success(t("tips.success"));
            },
          });
        }
      }
    },
    {
      label: t("commons.logout"),
      key: 'logout',
      props: {
        onClick: () => Dialog.info({
          title: t("commons.logout"),
          content: t("tips.logoutConfirm"),
          positiveText: t("commons.confirm"),
          negativeText: t("commons.cancel"),
          onPositiveClick: async () => {
            await userStore.logout();
            Message.success(t('commons.logoutSuccess'));
            await router.push({ name: "login" });
          }
        })
      }
    }
  ];
  return options;
}

const resetPassword = () => {
  popupResetUserPasswordDialog(
    async (password: string) => {
      await resetUserPasswordApi(userStore.user!.id, password);
    },
    () => { Message.info(t("tips.resetUserPasswordSuccess")) },
    () => { Message.error(t("tips.resetUserPasswordFailed")) }
  )
}

const jumpToAdminOrConv = async () => {
  if (isInAdmin.value) {
    await router.push({ name: 'conversation' });
  } else {
    await router.push({ name: 'admin' });
  }
}



</script>

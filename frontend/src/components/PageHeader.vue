<template>
  <n-page-header>
    <template #title>
      <n-space :align="'center'">
        <div>
          <a href="#" style="text-decoration: none; color: inherit">{{ $t("commons.siteTitle") }}</a>
        </div>
        <div>
          <a class="h-full inline-block flex" href="https://github.com/moeakwak/chatgpt-web-share" target="_blank">
            <n-icon :color="appStore.theme == 'dark' ? 'white' : 'black'" :component="LogoGithub" />
          </a>
        </div>
      </n-space>
    </template>
    <template #avatar>
      <n-avatar src="/chatgpt-icon.svg" />
    </template>
    <template #extra>
      <n-space>
        <div>
          <div v-if="userStore.user" class="inline-block">
            <span>Hi, {{ userStore.user.nickname }}</span>
            <n-dropdown :options="options" placement="bottom-start">
              <n-button circle class="ml-3">
                <n-icon :component="SettingsSharp" />
              </n-button>
            </n-dropdown>

          </div>
          <div v-else class="text-gray-500 inline-block">{{ $t("commons.notLogin") }}</div>
          <n-button circle class="ml-3" @click="toggleTheme">
            <n-icon :component="themeIcon" />
          </n-button>
          <n-dropdown :options="languageOptions" placement="bottom-start">
            <n-button circle class="ml-3">
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
import { DarkModeRound, LightModeRound } from '@vicons/material';
import { useI18n } from 'vue-i18n';
import { Dialog, Message } from '@/utils/tips';
import router from '@/router';
import { DropdownOption } from "naive-ui"
import { ref, computed, h } from 'vue';
import UserProfileCard from './UserProfileCard.vue';


const { t } = useI18n();
const userStore = useUserStore();
const appStore = useAppStore();

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

const options = ref<Array<DropdownOption>>([
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
    label: t("commons.logout"),
    key: 'logout',
    props: {
      onClick: () => Dialog.info({
        title: t("commons.logout"),
        content: t("tips.logoutConfirm"),
        positiveText: t("commons.confirm"),
        negativeText: t("commons.cancel"),
        onPositiveClick: () => userStore.logout().then(() => {
          Message.success(t('commons.logoutSuccess'));
          router.push({ path: '/' });
        }),
      })
    }
  }
])

if (userStore.user?.is_superuser) {
  options.value.unshift({
    label: t("commons.adminPanel"),
    show: userStore.user?.is_superuser,
    key: 'admin',
    props: {
      onClick: () => router.push({ name: 'admin' })
    }
  })
}

</script>

<template>
  <n-page-header>
    <template #title>
      <a href="#" style="text-decoration: none; color: inherit">{{ $t("commons.siteTitle") }}</a>
    </template>
    <template #avatar>
      <n-avatar src="/chatgpt-icon.svg" />
    </template>
    <template #extra>
      <n-space>
        <div v-if="userStore.user">
          <span>Hi, {{ userStore.user.nickname }}</span>
          <n-dropdown :options="options" placement="bottom-start">
            <n-button circle class="ml-3">
              <n-icon :component="SettingsSharp" />
            </n-button>
          </n-dropdown>
        </div>
        <div v-else class="text-gray-500">{{ $t("commons.notLogin") }}</div>
      </n-space>
    </template>
  </n-page-header>
</template>

<script setup lang="ts">
import { useUserStore } from '@/store';
import { SettingsSharp } from '@vicons/ionicons5';
import { useI18n } from 'vue-i18n';
import { Dialog, Message } from '@/utils/tips';
import router from '@/router';
import { DropdownOption } from "naive-ui"
import { ref, h } from 'vue';
import UserProfileCard from './UserProfileCard.vue';

const { t } = useI18n();
const userStore = useUserStore();
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

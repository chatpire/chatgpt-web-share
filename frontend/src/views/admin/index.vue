<template>
  <n-space
    vertical
    class="-ml-2 h-full px-2"
  >
    <n-layout
      has-sider
      class="h-90vh"
    >
      <n-layout-sider
        bordered
        :collapsed="collapsed"
        collapse-mode="width"
        :collapsed-width="64"
        :width="200"
        show-trigger
        @collapse="collapsed = true"
        @expand="collapsed = false"
      >
        <n-menu
          v-model:value="activeKey"
          :collapsed-width="64"
          :collapsed-icon-size="22"
          :options="menuOptions"
        />
      </n-layout-sider>
      <n-layout class="ml-4 mr-2">
        <n-scrollbar>
          <router-view v-slot="{ Component, route }">
            <keep-alive>
              <component
                :is="Component"
                :key="route.fullPath"
              />
            </keep-alive>
          </router-view>
        </n-scrollbar>
      </n-layout>
    </n-layout>
  </n-space>
</template>

<script setup lang="ts">
import { ChatbubbleEllipses, FileTrayFull, InformationCircle } from '@vicons/ionicons5';
import { SettingsRound, SupervisedUserCircleRound } from '@vicons/material';
import { NIcon } from 'naive-ui';
import { h, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';
const { t } = useI18n();
const router = useRouter();

const collapsed = ref(true);
const activeKey = ref<string>(router.currentRoute.value.name as string);

function renderIcon(icon: any) {
  return () => h(NIcon, null, { default: () => h(icon) });
}

const menuOptions = [
  {
    label: t('commons.systemManagement'),
    key: 'systemManagement',
    icon: renderIcon(InformationCircle),
  },
  {
    label: t('commons.userManagement'),
    key: 'userManagement',
    icon: renderIcon(SupervisedUserCircleRound),
  },
  {
    label: t('commons.conversationManagement'),
    key: 'conversationManagement',
    icon: renderIcon(ChatbubbleEllipses),
  },
  {
    label: t('commons.logViewer'),
    key: 'logViewer',
    icon: renderIcon(FileTrayFull),
  },
  {
    label: t('commons.configManager'),
    key: 'configManagement',
    icon: renderIcon(SettingsRound),
  },
];

watch(
  async () => activeKey.value,
  (_newName: any) => {
    router.push({ name: activeKey.value });
  }
);
</script>

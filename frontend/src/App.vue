<template>
  <n-config-provider :locale="locale" :theme="theme">
    <n-global-style />
    <div class="w-full box-border flex flex-col">
      <n-layout>
        <PageHeader v-if="userStore.user" />
        <div style="height: calc(100vh - var(--header-height)); height: calc(100dvh - var(--header-height))">
          <router-view />
        </div>
      </n-layout>
    </div>
  </n-config-provider>
</template>

<script setup lang="ts">
import { useEventListener } from '@vueuse/core';
import { darkTheme, enUS, zhCN } from 'naive-ui';
import { computed } from 'vue';

import PageHeader from './components/PageHeader.vue';
import { useAppStore, useUserStore } from './store';

const appStore = useAppStore();
const userStore = useUserStore();

const setFullHeight = () => {
  const headerHeight = parseInt(getComputedStyle(document.documentElement).getPropertyValue('--header-height'), 10);
  const windowHeight = window.innerHeight;
  // 动态计算并设置高度
  document.documentElement.style.setProperty('--full-height', `${windowHeight - headerHeight}px`);
};

useEventListener('resize', setFullHeight);

const theme = computed(() => {
  if (appStore.theme == 'dark') {
    return darkTheme;
  } else {
    return {};
  }
});

const locale = computed(() => {
  if (appStore.language == 'zh-CN') return zhCN;
  else return enUS;
});
</script>

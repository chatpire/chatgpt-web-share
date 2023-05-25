<template>
  <n-config-provider :theme="theme">
    <n-global-style />
    <div class="w-full box-border min-h-screen flex flex-col">
      <n-layout>
        <PageHeader />
        <div style="height: calc(100vh - var(--header-height));">
          <router-view />
        </div>
      </n-layout>
    </div>
  </n-config-provider>
</template>

<script setup lang="ts">
import { darkTheme } from 'naive-ui';
import { computed } from 'vue';

import PageHeader from './components/PageHeader.vue';
import { useAppStore } from './store';

const appStore = useAppStore();

const theme = computed(() => {
  if (appStore.theme == 'dark') {
    return darkTheme;
  } else {
    return {};
  }
});
</script>

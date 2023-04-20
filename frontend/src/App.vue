<template>
  <n-config-provider :theme="theme">
    <n-global-style />
    <div class="w-full box-border min-h-screen flex flex-col">
      <div class="my-4 px-4">
        <PageHeader />
      </div>
      <router-view />
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

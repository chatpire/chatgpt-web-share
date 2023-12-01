<template>
  <div class="mb-4 flex flex-col">
    <n-tabs v-model:value="tab" type="segment">
      <n-tab-pane name="completions" :tab="t('commons.completionLogs')">
        <CompletionLogContent />
      </n-tab-pane>
      <n-tab-pane name="server" :tab="t('commons.serverLogs')">
        <ServerLogContent />
      </n-tab-pane>
    </n-tabs>
  </div>
</template>

<script setup lang="ts">
import { nextTick, onUnmounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { getServerLogsApi } from '@/api/logs';
import { LogFilterOptions } from '@/types/schema';

import CompletionLogContent from '../components/CompletionLogContent.vue';
import ServerLogContent from '../components/ServerLogContent.vue';
const { t } = useI18n();

const refresh_duration = ref(5);
const tab = ref<string>('completions');
const logsContent = ref<Array<string>>();
const enableAutoScroll = ref(true);
const maxLineCount = ref(100);
const proxyExcludeKeywords = ref<Array<string>>([]);
const serverExcludeKeywords = ref<Array<string>>(['status', 'logs']);

const logInstRef = ref();

watch(
  () => tab.value,
  () => {
    loadLogs();
  }
);
watch(
  () => maxLineCount.value,
  () => {
    loadLogs();
  }
);

const scrollToBottom = () => {
  nextTick(() => {
    logInstRef.value?.scrollTo({ position: 'bottom', slient: false });
  });
};

const loadLogs = () => {
  if (tab.value === 'server') {
    getServerLogsApi({
      max_lines: maxLineCount.value,
      exclude_keywords: serverExcludeKeywords.value,
    } as LogFilterOptions).then((res) => {
      logsContent.value = res.data;
    });
  }
  if (enableAutoScroll.value) {
    scrollToBottom();
  }
};

loadLogs();
let interval = setInterval(() => {
  loadLogs();
}, refresh_duration.value * 1000);

onUnmounted(() => {
  // 添加这个部分，这样组件卸载时会清除定时器
  clearInterval(interval);
});

watch(
  () => refresh_duration.value,
  () => {
    clearInterval(interval);
    interval = setInterval(() => {
      loadLogs();
    }, refresh_duration.value * 1000);
  }
);

watch(
  () => serverExcludeKeywords.value,
  () => {
    loadLogs();
  }
);

watch(
  () => proxyExcludeKeywords.value,
  () => {
    loadLogs();
  }
);
</script>

<style>
.option-item {
  @apply flex flex-row space-x-2 items-center mr-1 my-1;
}
</style>

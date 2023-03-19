<template>
  <div class="mb-4 h-full flex flex-col">
    <n-tabs type="segment" v-model:value="tab">
      <n-tab name="server">{{ t("commons.serverLogs") }}</n-tab>
      <n-tab name="proxy">{{ t("commons.proxyLogs") }}</n-tab>
    </n-tabs>
    <!-- 一个selector用于切换更新频率 -->
    <div class="flex flex-row mt-3 justify-between">
      <div class="flex flex-row space-x-3">
        <div class="my-auto"><n-text>{{ t("commons.maxLineCount") }}</n-text></div>
        <n-input-number size="small" v-model:value="maxLineCount" class="w-30" :min="100" :max="2000" :step="100" />
        <div class="my-auto"><n-text>{{ t("commons.updateInterval") }}</n-text></div>
        <n-select size="small" v-model:value="refresh_duration" prefix="1" class="w-20" :options="[
          { label: '3s', value: 3 },
          { label: '5s', value: 5 },
          { label: '10s', value: 10 },
        ]"></n-select>
      </div>
      <div class="flex flex-row space-x-3">
        <div class="my-auto"><n-text>{{ t("commons.autoScrolling") }}</n-text></div>
        <div class="my-auto"><n-switch v-model:value="enableAutoScroll" size="small" /></div>
      </div>
    </div>
    <n-card class="mt-3" :content-style="{ height: '100%' }">
      <n-scrollbar ref="scrollRef" class="h-120 relative">
        <div class="whitespace-pre-line font-mono text-[0.2rem]">
          {{ filteredLogsContent }}
        </div>
      </n-scrollbar>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { getProxyLogsApi, getServerLogsApi } from '@/api/status';
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
const { t } = useI18n();

const scrollRef = ref();
const refresh_duration = ref(5);
const tab = ref('server');
const logsContent = ref<string>();
const enableAutoScroll = ref(true);
const maxLineCount = ref(100);

const filteredLogsContent = computed(() => {
  // 过滤含有/logs/server的行
  return logsContent.value?.split('\n').filter((line) => !line.includes('/logs')).join('\n');
});

watch(() => tab.value, () => {
  loadLogs();
});
watch(() => maxLineCount.value, () => {
  loadLogs();
});

const loadLogs = () => {
  if (tab.value === 'server') {
    getServerLogsApi(maxLineCount.value).then((res) => {
      logsContent.value = res.data;
    });
  } else {
    getProxyLogsApi(maxLineCount.value).then((res) => {
      logsContent.value = res.data;
    });
  }
  if (enableAutoScroll.value)
    scrollRef.value?.scrollTo({ left: 0, top: scrollRef.value.$refs.scrollbarInstRef.contentRef.scrollHeight, behavior: 'smooth' });
}

loadLogs();
let interval = setInterval(() => {
  loadLogs();
}, refresh_duration.value * 1000);

watch(() => refresh_duration.value, () => {
  clearInterval(interval);
  interval = setInterval(() => {
    loadLogs();
  }, refresh_duration.value * 1000);
});

</script>
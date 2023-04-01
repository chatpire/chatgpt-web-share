<template>
  <div class="mb-4 h-full flex flex-col">
    <n-tabs type="segment" v-model:value="tab">
      <n-tab name="server">{{ t("commons.serverLogs") }}</n-tab>
      <n-tab name="proxy">{{ t("commons.proxyLogs") }}</n-tab>
    </n-tabs>
    <!-- 设置 -->
    <div class="flex flex-row mt-3 justify-between">
      <div class="flex flex-wrap flex-row sm:space-x-3">
        <div class="option-item"><n-text>{{ t("commons.maxLineCount") }}</n-text>
          <n-input-number size="small" v-model:value="maxLineCount" class="w-27" :min="100" :max="2000" :step="100" />
        </div>
        <div class="option-item"><n-text>{{ t("commons.updateInterval") }}</n-text>
          <n-select size="small" v-model:value="refresh_duration" class="w-20" :options="[
            { label: '3s', value: 3 },
            { label: '5s', value: 5 },
            { label: '10s', value: 10 },
          ]"></n-select>
        </div>
        <div class="option-item"><n-text>{{ t("commons.excludeKeywords") }}</n-text>
          <n-dynamic-tags v-if="tab === 'proxy'" size="small" v-model:value="proxyExcludeKeywords"></n-dynamic-tags>
          <n-dynamic-tags v-else size="small" v-model:value="serverExcludeKeywords"></n-dynamic-tags>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <n-text>{{ t("commons.autoScrolling") }}</n-text>
        <n-switch v-model:value="enableAutoScroll" size="small" />
      </div>
    </div>
    <n-card class="mt-3 flex-grow h-full" :content-style="{ height: '100%' }">
      <n-scrollbar ref="scrollRef" class="h-160 relative">
        <!-- <div class="whitespace-pre-line font-mono text-[0.2em]">
          {{ filteredLogsContent }}
        </div> -->
        <n-log :font-size="10" :rows="maxLineCount" :lines="logsContent" />
      </n-scrollbar>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { getServerLogsApi, getProxyLogsApi } from '@/api/system';
import { LogFilterOptions } from '@/types/schema';
import { ref, computed, watch } from 'vue';
import { useI18n } from 'vue-i18n';
const { t } = useI18n();

const scrollRef = ref();
const refresh_duration = ref(5);
const tab = ref<string>('server');
const logsContent = ref<Array<string>>();
const enableAutoScroll = ref(true);
const maxLineCount = ref(100);
const proxyExcludeKeywords = ref<Array<string>>([])
const serverExcludeKeywords = ref<Array<string>>([
  "status",
  "logs"
])

// const filteredLogsContent = computed(() => {
//   // 过滤含有/logs/server的行
//   return logsContent.value?.join('');
// });

watch(() => tab.value, () => {
  loadLogs();
});
watch(() => maxLineCount.value, () => {
  loadLogs();
});

const loadLogs = () => {
  if (tab.value === 'server') {
    getServerLogsApi({
      max_lines: maxLineCount.value,
      exclude_keywords: serverExcludeKeywords.value,
    } as LogFilterOptions).then((res) => {
      logsContent.value = res.data;
    });
  } else {
    getProxyLogsApi({
      max_lines: maxLineCount.value,
      exclude_keywords: proxyExcludeKeywords.value,
    } as LogFilterOptions).then((res) => {
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

watch(() => serverExcludeKeywords.value, () => {
  loadLogs();
});

watch(() => proxyExcludeKeywords.value, () => {
  loadLogs();
});

</script>

<style>
.option-item {
  @apply flex flex-row space-x-2 items-center mr-1 my-1;
}
</style>
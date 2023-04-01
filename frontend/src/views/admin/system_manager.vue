<template>
  <div class="mb-4 mt-2 flex flex-col space-y-4">
    <SystemInfoCard :system-info="systemInfo" :server-status="serverStatus" />
    <StatisticsCard :request-statistics="requestStatistics"  />
  </div>
</template>

<script setup lang="ts">
import { getServerStatusApi } from '@/api/status';
import { getSystemInfoApi, getRequestStatisticsApi } from '@/api/system';
import { ServerStatusSchema, SystemInfo, RequestStatistics } from '@/types/schema';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import StatisticsCard from './components/StatisticsCard.vue';
import SystemInfoCard from './components/SystemInfoCard.vue';
const { t } = useI18n();

const systemInfo = ref<SystemInfo | undefined>();
const serverStatus = ref<ServerStatusSchema | undefined>();
const requestStatistics = ref<RequestStatistics | undefined>();

getSystemInfoApi().then((res) => {
  systemInfo.value = res.data;
});

getServerStatusApi().then((res) => {
  serverStatus.value = res.data;
});

getRequestStatisticsApi().then((res) => {
  requestStatistics.value = res.data;
});
</script>


<template>
  <div class="flex flex-col space-y-4">
    <SystemInfoCard :system-info="systemInfo" :server-status="serverStatus" @refresh="refreshData" />
    <StatisticsCard :request-stats="requestStats" :ask-stats="askStats" :users="users" :granularity="granularity" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { getServerStatusApi } from '@/api/status';
import { getAskStatisticsApi, getRequestStatisticsApi, getSystemInfoApi } from '@/api/system';
import { getAllUserApi } from '@/api/user';
import { AskLogAggregation, CommonStatusSchema, RequestLogAggregation, SystemInfo, UserRead } from '@/types/schema';

import StatisticsCard from '../components/StatisticsCard.vue';
import SystemInfoCard from '../components/SystemInfoCard.vue';
const { t } = useI18n();

const systemInfo = ref<SystemInfo | undefined>();
const serverStatus = ref<CommonStatusSchema | undefined>();
const requestStats = ref<RequestLogAggregation[] | undefined>();
const askStats = ref<AskLogAggregation[] | undefined>();
const users = ref<UserRead[] | undefined>();

const granularity = 1800;

const refreshData = () => {
  getSystemInfoApi().then((res) => {
    systemInfo.value = res.data;
  });

  getServerStatusApi().then((res) => {
    serverStatus.value = res.data;
  });

  getRequestStatisticsApi(granularity).then((res) => {
    requestStats.value = res.data;
  });

  getAskStatisticsApi(granularity).then((res) => {
    askStats.value = res.data;
  });
};

refreshData();

getAllUserApi().then((res) => {
  users.value = res.data;
});
</script>

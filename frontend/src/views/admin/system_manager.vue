<template>
  <div class="mb-4 mt-2 flex flex-col space-y-4">
    <SystemInfoCard :system-info="systemInfo" :server-status="serverStatus" @refresh="refreshData" />
    <StatisticsCard :request-statistics="requestStatistics" :users="users" />
  </div>
</template>

<script setup lang="ts">
import { getServerStatusApi } from '@/api/status';
import { getSystemInfoApi, getRequestStatisticsApi } from '@/api/system';
import { getAllUserApi } from '@/api/user';
import { ServerStatusSchema, SystemInfo, RequestStatistics, UserRead } from '@/types/schema';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import StatisticsCard from './components/StatisticsCard.vue';
import SystemInfoCard from './components/SystemInfoCard.vue';
import { Message } from '@/utils/tips';
const { t } = useI18n();

const systemInfo = ref<SystemInfo | undefined>();
const serverStatus = ref<ServerStatusSchema | undefined>();
const requestStatistics = ref<RequestStatistics | undefined>();
const users = ref<UserRead[] | undefined>();

const refreshData = () => {
  getSystemInfoApi().then((res) => {
    systemInfo.value = res.data;
  });

  getServerStatusApi().then((res) => {
    serverStatus.value = res.data;
  });

  getRequestStatisticsApi().then((res) => {
    requestStatistics.value = res.data;
  });
}

refreshData();

getAllUserApi().then((res) => {
  users.value = res.data;
})
</script>


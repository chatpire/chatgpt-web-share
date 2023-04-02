<template>
  <n-card :title="t('commons.statisticsInfo')" :content-style="{ padding: '0px'}" :header-style="{ paddingBottom: 0 }" >
    <RequestsChart :users="users" :loading="loading" :request-counts-interval="requestCountsInterval" :request-counts="requestCounts" />
  </n-card>
</template>

<script setup lang="ts">
import { getSystemInfoApi } from '@/api/system';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import RequestsChart from './charts/RequestsChart.vue';
import { ServerStatusSchema, SystemInfo, RequestStatistics, UserRead } from '@/types/schema';
const { t } = useI18n();

const props = defineProps<{
  requestStatistics?: RequestStatistics;
  users?: UserRead[];
}>();

const loading = computed(() => {
  return !props.requestStatistics;
})

const requestCountsInterval = computed(() => {
  return props.requestStatistics?.request_counts_interval;
})

const requestCounts = computed(() => {
  return props.requestStatistics?.request_counts as any;
})
</script>
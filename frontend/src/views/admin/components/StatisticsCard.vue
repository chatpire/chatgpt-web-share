<template>
  <n-card :title="t('commons.statisticsInfo')" :content-style="{ padding: '0px' }" :header-style="{ paddingBottom: 0 }">
    <RequestsChart
      :users="users"
      :loading="loading"
      :request-stats-granularity="$props.granularity"
      :request-stats="requestStats || []"
    />

    <AskChart :loading="loading" :ask-stats="askStats || []" :granularity="granularity" :users="users" />
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { AskLogAggregation, RequestLogAggregation, UserRead } from '@/types/schema';

import AskChart from './charts/AskChart.vue';
import RequestsChart from './charts/RequestsChart.vue';
const { t } = useI18n();

const props = defineProps<{
  requestStats?: RequestLogAggregation[];
  askStats?: AskLogAggregation[];
  users?: UserRead[];
  granularity: number;
}>();

const loading = computed(() => {
  return !props.requestStats;
});
</script>

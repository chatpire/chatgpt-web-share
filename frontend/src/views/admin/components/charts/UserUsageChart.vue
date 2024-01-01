<template>
  <v-chart ref="chartRef" class="h-20" :option="option" :loading="props.loading" />
</template>

<script setup lang="ts">
import { EChartsOption } from 'echarts';
import { BarChart } from 'echarts/charts';
import { GridComponent, LegendComponent, TitleComponent, TooltipComponent } from 'echarts/components';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { computed, onMounted, ref } from 'vue';
import VChart from 'vue-echarts';
import { useI18n } from 'vue-i18n';

import { useAppStore } from '@/store';
import { AskLogDocument, UserReadAdmin } from '@/types/schema';

const { t } = useI18n();
const appStore = useAppStore();

use([TitleComponent, CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent]);

const chartRef = ref<InstanceType<typeof VChart>>();

const props = defineProps<{
  loading: boolean;
  askLogs: AskLogDocument[];
  users?: UserReadAdmin[];
}>();

const modelPrefixes = ['gpt_4'];

const userIds = computed(() => {
  const userIds = new Set<number>();
  props.askLogs.forEach((log) => {
    userIds.add(log.user_id);
  });
  return Array.from(userIds);
});

const timeRangeTitle = computed(() => {
  // 查找所有 log.time (string) 的最大值和最小值，给出图表标题
  const times = props.askLogs.map((log) => new Date(log.time!).getTime());
  const min = Math.min(...times);
  const max = Math.max(...times);
  const total = props.askLogs.length;
  return `GPT-4 Count    (${new Date(min).toLocaleString()} ~ ${new Date(max).toLocaleString()})    Total: ${total}`;
});

function groupByModel(askLogs: AskLogDocument[]) {
  const modelMap: Record<string, Record<number, number>> = {};
  for (const prefix of modelPrefixes) {
    modelMap[prefix] = {};
  }

  askLogs.forEach((log) => {
    const model = log.meta.model;
    const userId = log.user_id;
    if (modelPrefixes.some((prefix) => model.startsWith(prefix))) {
      const prefix = modelPrefixes.find((prefix) => model.startsWith(prefix))!;
      if (!modelMap[prefix]) {
        modelMap[prefix] = {};
      }
      if (!modelMap[prefix][userId]) {
        modelMap[prefix][userId] = 0;
      }
      modelMap[prefix][userId]++;
    }
  });

  return modelMap;
}

const series = computed(() => {
  const groupedData = groupByModel(props.askLogs);
  // console.log(groupedData);
  const modelTotals = modelPrefixes.reduce(
    (acc, prefix) => {
      acc[prefix] = 0;
      Object.values(groupedData[prefix]).forEach((count) => {
        acc[prefix] += count;
      });
      return acc;
    },
    {} as Record<string, number>
  );

  const series = [];

  for (const userId of userIds.value) {
    const data = modelPrefixes.map((prefix) => {
      const value = groupedData[prefix][userId] || 0;
      const total = modelTotals[prefix];
      const percentage = total > 0 ? (value / total) * 100 : 0.0;
      return {
        value,
        label: {
          show: true,
          formatter: percentage > 5 ? '{c} (' + `${percentage.toFixed(1)}%` + ')' : '{c}',
          position: 'inside',
        },
        userId,
        model: prefix,
      };
    });

    if (data.some((d) => d.value !== null)) {
      series.push({
        name: findUsername(userId),
        type: 'bar',
        stack: 'total',
        emphasis: {
          focus: 'series',
        },
        data,
      });
    }
  }

  series.sort((a, b) => {
    const gpt4a = a.data.find((d) => d.model === 'gpt_4')?.value || 0;
    const gpt4b = b.data.find((d) => d.model === 'gpt_4')?.value || 0;
    return gpt4b - gpt4a;
  });

  return series;
});

const findUsername = (userId: number) => {
  const user = props.users?.find((u) => u.id === userId);
  return user?.username || `User ${userId}`;
};

const isDark = computed(() => appStore.theme === 'dark');

const option = computed<EChartsOption>(() => {
  return {
    title: {
      text: timeRangeTitle.value,
      left: 'center',
      top: '0%',
      textStyle: {
        color: isDark.value ? '#DDD' : '#4E5969',
        fontSize: 14,
        fontWeight: 500,
      },
    },
    grid: {
      left: '2%',
      right: '2%',
      top: '25%',
      bottom: '4%',
      // containLabel: true,
    },
    tooltip: {
      trigger: 'item',
    },
    legend: {
      show: false,
      textStyle: {
        color: isDark.value ? '#EDEDED' : '#4E5969',
      },
      orient: 'vertical',
      right: 10,
    },
    xAxis: {
      type: 'value',
      show: false,
      max: 'dataMax',
    },
    yAxis: {
      type: 'category',
      data: modelPrefixes,
      show: false,
    },
    series: series.value,
  } as EChartsOption;
});

onMounted(() => {
  chartRef.value?.resize();
});
</script>

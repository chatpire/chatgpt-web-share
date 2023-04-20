<template>
  <div class="pr-4">
    <v-chart
      class="h-60"
      :option="option"
      :loading="props.loading"
    />
  </div>
</template>

<script setup lang="ts">
import { BarSeriesOption } from 'echarts';
import { BarChart } from 'echarts/charts';
import {
  BrushComponent,
  DatasetComponent,
  DataZoomComponent,
  GridComponent,
  LegendComponent,
  TitleComponent,
  ToolboxComponent,
  TooltipComponent,
} from 'echarts/components';
import { use } from 'echarts/core';
import { CanvasRenderer } from 'echarts/renderers';
import { computed, ref } from 'vue';
import VChart from 'vue-echarts';
import { useI18n } from 'vue-i18n';

import { useAppStore } from '@/store';
import { ToolTipFormatterParams } from '@/types/echarts';
import { UserRead } from '@/types/schema';

import { timeFormatter } from './helpers';
const { t } = useI18n();
const appStore = useAppStore();

use([
  TitleComponent,
  CanvasRenderer,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  DatasetComponent,
  DataZoomComponent,
  ToolboxComponent,
  BrushComponent,
]);

type AskRecord = [[number, string, number, number], number];

// provide(THEME_KEY, appStore.theme);
interface StatRecord {
  timestamp: number;
  count: number;
  sumAskDuration: number;
  sumTotalDuration: number;
  userIds: number[];
}

const props = defineProps<{
  loading: boolean;
  askRecords?: AskRecord[];
  users?: UserRead[];
}>();

function makeDataset(askRecords: AskRecord[]) {
  // 获得最早的时间戳
  const earliestTimestamp = askRecords.reduce((min, record) => Math.min(min, record[1]), Number.MAX_VALUE);

  const latestTimestamp = askRecords.reduce((max, record) => Math.max(max, record[1]), Number.MIN_VALUE);

  // 对齐到整点或半点
  const alignedEarliestTimestamp = Math.floor(earliestTimestamp / 1800) * 1800 * 1000;
  const alignedLatestTimestamp = Math.ceil(latestTimestamp / 1800) * 1800 * 1000;

  // 数据分类
  const otherRecords: AskRecord[] = [];
  const gpt4Records: AskRecord[] = [];

  askRecords.forEach((record) => {
    if (record[0][1] === 'gpt-4') {
      gpt4Records.push(record);
    } else {
      otherRecords.push(record);
    }
  });

  // 计算统计数据
  function calculateStats(records: AskRecord[]): StatRecord[] {
    const stats: StatRecord[] = [];
    let currentTimestamp = alignedEarliestTimestamp;
    // console.log('currentTimestamp', currentTimestamp, new Date(currentTimestamp).toLocaleString())
    while (currentTimestamp < alignedLatestTimestamp) {
      const recordsInInterval = records.filter((record) => record[1] * 1000 >= currentTimestamp && record[1] * 1000 < currentTimestamp + 1800 * 1000);

      if (recordsInInterval.length > 0) {
        const userIds = new Set(recordsInInterval.map((record) => record[0][0]));
        const stat: StatRecord = {
          timestamp: currentTimestamp,
          count: recordsInInterval.length,
          sumAskDuration: recordsInInterval.reduce((sum, record) => sum + record[0][2], 0),
          sumTotalDuration: recordsInInterval.reduce((sum, record) => sum + record[0][3], 0),
          userIds: Array.from(userIds),
        };
        stats.push(stat);
      } else {
        const stat: StatRecord = {
          timestamp: currentTimestamp,
          count: 0,
          sumAskDuration: 0,
          sumTotalDuration: 0,
          userIds: [],
        };
        stats.push(stat);
      }

      currentTimestamp += 1800 * 1000;
    }

    return stats;
  }

  const otherStats = calculateStats(otherRecords);
  const gpt4Stats = calculateStats(gpt4Records);

  return [{ source: otherStats }, { source: gpt4Stats }];
}

const dataset = computed(() => {
  if (props.askRecords) {
    return makeDataset(props.askRecords);
  } else {
    return [];
  }
});

const findUsername = (user_id: number) => {
  const user = props.users?.find((u) => u.id === user_id);
  return user?.username || user_id;
};

const isDark = computed(() => appStore.theme === 'dark');

const generateSeries = (name: string, lineColor: string, itemBorderColor: string, datasetIndex: number): BarSeriesOption => {
  return {
    type: 'bar',
    name,
    datasetIndex,
    yAxisIndex: 0,
    encode: {
      x: 'timestamp',
      y: 'count',
    },
    stack: 'total',
    itemStyle: {
      color: lineColor,
    },
    emphasis: {
      focus: 'series',
      itemStyle: {
        color: lineColor,
        borderWidth: 2,
        borderColor: itemBorderColor,
      },
    },
  };
};

const showDataZoom = ref(false);
const dataZoomOption = computed(() => {
  return showDataZoom.value
    ? [
      {
        type: 'slider',
        show: showDataZoom.value,
        xAxisIndex: 0,
        start: 0,
        end: 100,
        filterMode: 'filter',
      },
    ]
    : [];
});
const gridBottom = computed(() => {
  return showDataZoom.value ? '25%' : '5%';
});

const option = computed(() => {
  return {
    title: {
      text: t('commons.askRequestsCount'),
      left: 'center',
      top: '2.6%',
      textStyle: {
        color: isDark.value ? '#DDD' : '#4E5969',
        fontSize: 16,
        fontWeight: 500,
      },
    },
    grid: {
      left: '2.6%',
      right: '4',
      top: '40',
      bottom: gridBottom.value,
      containLabel: true,
    },
    dataset: dataset.value,
    xAxis: {
      type: 'time',
      axisLabel: {
        color: '#4E5969',
        formatter: (val: any) => timeFormatter(val, false),
        hideOverlap: true,
      },
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      splitLine: {
        show: true,
        // interval: (idx: number) => {
        //   if (idx === 0) return false;
        //   if (idx === xAxis.value.length - 1) return false;
        //   return true;
        // },
        lineStyle: {
          // type: 'dashed',
          color: isDark.value ? '#2E2E30' : '#E5E8EF',
        },
      },
      axisPointer: {
        show: true,
        lineStyle: {
          color: '#23ADFF',
          width: 2,
        },
      },
    },
    yAxis: [
      {
        type: 'value',
        position: 'left',
        axisLine: {
          show: false,
        },
        axisLabel: {
          formatter(value: number, idx: number) {
            if (idx === 0) return String(value);
            return `${value}`;
          },
        },
        splitLine: {
          lineStyle: {
            type: 'dashed',
            color: isDark.value ? '#2E2E30' : '#E5E8EF',
          },
        },
      },
    ],
    tooltip: {
      trigger: 'axis',
      formatter(params: any[]) {
        const [el0, el1] = params as ToolTipFormatterParams[];
        const data0 = el0.data as StatRecord;
        const data1 = el1.data as StatRecord;
        return `<div>
                  <span>${timeFormatter(data0.timestamp, true)} ~ ${timeFormatter(data0.timestamp + 1800 * 1000, true)}</span>
                  <br />
                  <span>${el0.seriesName}: ${data0.count}</span> <br />
                  <span>${el1.seriesName}: ${data1.count}</span> <br />
                  <span>${t('commons.normalAskUsers')}: ${data0.userIds.map((id: number) => findUsername(id))}</span> <br />
                  <span>${t('commons.gpt4AskUsers')}: ${data1.userIds.map((id: number) => findUsername(id))}</span> <br />
                  <span>${t('commons.sumOfNormalAskDuration')}: ${data0.sumAskDuration.toFixed(2)} s</span> <br />
                  <span>${t('commons.sumOfGpt4AskDuration')}: ${data1.sumAskDuration.toFixed(2)} s</span> <br />
                </div>`;
      },
      className: 'echarts-tooltip-diy',
    },

    series: [
      generateSeries(t('commons.normalAskCount'), '#9ce6aa', '#E8FFFB', 0),
      generateSeries(t('commons.gpt4AskCount'), '#F77234', '#FFE4BA', 1),
    ],

    toolbox: {
      feature: {
        myDataZoom: {
          show: true,
          title: 'DataZoom',
          icon: 'path://M0,0H12V2H0V0ZM0,14H12V16H0V14ZM0,6H12V8H0V6ZM0,10H12V12H0V10Z',
          onclick: () => {
            showDataZoom.value = !showDataZoom.value;
          },
        },
        restore: {},
        saveAsImage: {},
      },
    },
    dataZoom: dataZoomOption.value,
  };
});

// watchEffect(() => {
console.log('props', props.askRecords);
// console.log('xAxis', xAxis.value);
// console.log('totalRequestsCountData', totalRequestsCountData.value);
// console.log('datasetSource', datasetSource.value);
// console.log('users', props.users)
//   console.log('option', option.value);
// });
</script>

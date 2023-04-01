<template>
  <div class="pr-4">
    <v-chart class="h-60" :option="option" :loading="props.loading" />
  </div>
</template>

<script setup lang="ts">
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  TitleComponent,
  GridComponent,
  // GraphicComponent,
  TooltipComponent,
  LegendComponent
} from "echarts/components";
import VChart, { THEME_KEY } from "vue-echarts";
import { ToolTipFormatterParams } from '@/types/echarts';
import { ref, watchEffect, computed } from "vue";
import { LineSeriesOption } from 'echarts';
import { useAppStore } from "@/store";
import { useI18n } from "vue-i18n";
const { t } = useI18n();
const appStore = useAppStore();

use([
TitleComponent,
  CanvasRenderer,
  LineChart,
  GridComponent,
  // GraphicComponent,
  TooltipComponent,
  LegendComponent
]);

// provide(THEME_KEY, appStore.theme);

const tooltipItemsHtmlString = (items: any[]) => {
  return items
    .map(
      (el) => `<div class="content-panel">
          <span>${el.seriesName}: ${el.value}</span>
      </div>`
    )
    .join('');
};

const props = defineProps<{
  loading: boolean;
  requestCounts?: [number, number][];
  requestCountsInterval?: number;
  // askRequestCountData: [[string, number], number][];
}>();

const isDark = computed(() => appStore.theme === 'dark');
const xAxis = computed(() => {
  return props.requestCounts?.map(([timestage, _]) => {
    const date = new Date(timestage * 1000 * props.requestCountsInterval!);
    const month = (date.getMonth() + 1).toString().padStart(2, '0')
    const day = date.getDate().toString().padStart(2, '0')
    const hour = date.getHours().toString().padStart(2, '0')
    const minute = date.getMinutes().toString().padStart(2, '0')
    return `${month}-${day} ${hour}:${minute}`

  }) || [];
})
const totalRequestsCountData = computed(() => {
  return props.requestCounts?.map(([_, count]) => count) || [];
});
// const askRequestCountData = computed(() => {
//   props.askRequestCountData.map(([_, count]) => count);
// });

watchEffect(() => {
  console.log('props', props.requestCounts);
  console.log('xAxis', xAxis.value);
  console.log('totalRequestsCountData', totalRequestsCountData.value);
  // console.log('askRequestCountData', askRequestCountData.value);
});

const generateSeries = (
  name: string,
  lineColor: string,
  itemBorderColor: string,
  data: number[]
): LineSeriesOption => {
  return {
    name,
    data,
    stack: 'Total',
    type: 'line',
    smooth: true,
    symbol: 'circle',
    symbolSize: 10,
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
    lineStyle: {
      width: 2,
      color: lineColor,
    },
    showSymbol: false,
    areaStyle: {
      opacity: 0.1,
      color: lineColor,
    },
  };
};

const option = computed(() => {
  return {
    title: {
      text: t("commons.totalRequestsCount"),
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
      bottom: '40',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      offset: 2,
      data: xAxis.value,
      boundaryGap: false,
      axisLabel: {
        color: '#4E5969',
        formatter(value: number, idx: number) {
          if (idx === 0) return '';
          if (idx === xAxis.value.length - 1) return '';
          return `${value}`;
        },
      },
      axisLine: {
        show: false,
      },
      axisTick: {
        show: false,
      },
      splitLine: {
        show: true,
        interval: (idx: number) => {
          if (idx === 0) return false;
          if (idx === xAxis.value.length - 1) return false;
          return true;
        },
        lineStyle: {
          type: 'dashed',
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
    yAxis: {
      type: 'value',
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
    tooltip: {
      trigger: 'axis',
      formatter(params: any[]) {
        const [firstElement] = params as ToolTipFormatterParams[];
        return `<div>
            <p class="tooltip-title">${firstElement.axisValueLabel}</p>
            ${tooltipItemsHtmlString(params as ToolTipFormatterParams[])}
          </div>`;
      },
      className: 'echarts-tooltip-diy',
    },
    series: [
      generateSeries(
        '总请求数',
        '#3469FF',
        '#E8F3FF',
        totalRequestsCountData.value
      ),
    ],
  }
})

</script>
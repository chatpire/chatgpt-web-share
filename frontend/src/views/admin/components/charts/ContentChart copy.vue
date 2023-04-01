<template>
  <v-chart class="h-100" :option="option" />
</template>

<script setup lang="ts">
import { use } from "echarts/core";
import { CanvasRenderer } from "echarts/renderers";
import { LineChart } from "echarts/charts";
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent
} from "echarts/components";
import VChart, { THEME_KEY } from "vue-echarts";
import { ref, provide } from "vue";
import { graphic } from 'echarts';

import { useAppStore } from "@/store";
const appStore = useAppStore();

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent
]);

provide(THEME_KEY, appStore.theme);

function graphicFactory(side: any) {
  return {
    type: 'text',
    bottom: '8',
    ...side,
    style: {
      text: '',
      textAlign: 'center',
      fill: '#4E5969',
      fontSize: 12,
    },
  };
}

const graphicElements = ref([
  graphicFactory({ left: '2.6%' }),
  graphicFactory({ right: 0 }),
]);

const xAxis = ref<string[]>(['a', 'b', 'c']);
const chartsData = ref<number[]>([1, 2, 3]);

const option = ref({
  grid: {
    left: '2.6%',
    right: '0',
    top: '10',
    bottom: '30',
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
        color: '#E5E8EF',
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
    // axisLabel: {
    //   formatter(value: any, idx: number) {
    //     return value;
    //   },
    // },
    splitLine: {
      show: true,
      lineStyle: {
        type: 'dashed',
        color: '#E5E8EF',
      },
    },
  },
  tooltip: {
    trigger: 'axis',
    formatter(params: any[]) {
      const [firstElement] = params;
      return `<div>
            <p class="tooltip-title">${firstElement.axisValueLabel}</p>
            <div class="content-panel"><span>总内容量</span><span class="tooltip-value">${(
          Number(firstElement.value) * 10000
        ).toLocaleString()}</span></div>
          </div>`;
    },
  },
  legend: {
    orient: "vertical",
    left: "left",
    data: ["Direct", "Email", "Ad Networks", "Video Ads", "Search Engines"]
  },
  graphic: {
    elements: graphicElements.value,
  },
  series: [
    {
      data: chartsData.value,
      type: 'line',
      smooth: true,
      // symbol: 'circle',
      symbolSize: 12,
      emphasis: {
        focus: 'series',
        itemStyle: {
          borderWidth: 2,
        },
      },
      lineStyle: {
        width: 3,
        color: new graphic.LinearGradient(0, 0, 1, 0, [
          {
            offset: 0,
            color: 'rgba(30, 231, 255, 1)',
          },
          {
            offset: 0.5,
            color: 'rgba(36, 154, 255, 1)',
          },
          {
            offset: 1,
            color: 'rgba(111, 66, 251, 1)',
          },
        ]),
      },
      showSymbol: false,
      areaStyle: {
        opacity: 0.8,
        color: new graphic.LinearGradient(0, 0, 0, 1, [
          {
            offset: 0,
            color: 'rgba(17, 126, 255, 0.16)',
          },
          {
            offset: 1,
            color: 'rgba(17, 128, 255, 0)',
          },
        ]),
      },
    },
  ],
});
</script>

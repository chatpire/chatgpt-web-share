<template>
  <div class="pr-4">
    <v-chart class="h-50" :option="option" :loading="props.loading" />
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
  LegendComponent,
  DatasetComponent,
  DataZoomComponent,
  ToolboxComponent,
  BrushComponent,
} from "echarts/components";
import VChart, { THEME_KEY } from "vue-echarts";
import { ToolTipFormatterParams } from '@/types/echarts';
import { ref, watchEffect, computed } from "vue";
import { LineSeriesOption } from 'echarts';
import { useAppStore } from "@/store";
import { useI18n } from "vue-i18n";
import { UserRead } from "@/types/schema";
const { t } = useI18n();
const appStore = useAppStore();

use([
  TitleComponent,
  CanvasRenderer,
  LineChart,
  GridComponent,
  // GraphicComponent,
  TooltipComponent,
  LegendComponent,
  DatasetComponent,
  DataZoomComponent,
  ToolboxComponent,
  BrushComponent
]);

// provide(THEME_KEY, appStore.theme);

const props = defineProps<{
  loading: boolean;
  requestCounts?: Record<string, [number, number[]]>; // list of [timestage, [total, user_id_list]]
  requestCountsInterval?: number;
  users?: UserRead[];
}>();

const findUsername = (user_id: number) => {
  const user = props.users?.find((u) => u.id === user_id);
  return user?.username || user_id;
};

const isDark = computed(() => appStore.theme === 'dark');

const datasetSource = computed(() => {
  const data = props.requestCounts ? Object.keys(props.requestCounts).map((key) => {
    const timestamp = parseInt(key) * 1000 * props.requestCountsInterval!;
    const count = props.requestCounts![key][0];
    const userIds = props.requestCounts![key][1] as number[];
    // const userString = userIds.map((i) => `${i}`).join(', ');
    return {
      timestamp,
      count,
      userIds
    }
  }) : [];
  return data;
});

const generateSeries = (
  name: string,
  lineColor: string,
  itemBorderColor: string,
): LineSeriesOption => {
  return {
    type: 'line',
    name,
    encode: {
      x: 'timestamp',
      y: 'count'
    },
    stack: 'Total',
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

const timeFormatter = (value: number) => {
  const date = new Date(value);
  const month = (date.getMonth() + 1).toString().padStart(2, '0')
  const day = date.getDate().toString().padStart(2, '0')
  const hour = date.getHours().toString().padStart(2, '0')
  const minute = date.getMinutes().toString().padStart(2, '0')
  return `${month}-${day} ${hour}:${minute}`
}

const showDataZoom = ref(false);
const dataZoomOption = computed(() => {
  return showDataZoom.value ? [
      {
        type: 'slider',
        show: showDataZoom.value,
        xAxisIndex: 0,
        start: 0,
        end: 100,
        filterMode: 'filter'
      }
    ] : [];
})
const gridBottom = computed(() => {
  return showDataZoom.value ? '25%' : '5%';
})

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
      bottom: gridBottom.value,
      containLabel: true
    },
    dataset: {
      source: datasetSource.value,
    },
    xAxis: {
      type: 'time',
      axisLabel: {
        color: '#4E5969',
        formatter: timeFormatter,
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
        const [el] = params as ToolTipFormatterParams[];
        const data = el.data as any;
        return `<div>
                  <span>${timeFormatter(data.timestamp)} ~ ${timeFormatter(data.timestamp + props.requestCountsInterval! * 1000)}</span>
                  <br />
                  <span>${el.seriesName}: ${data.count}</span> <br />
                  <span>${t("commons.requestUsers")}: ${data.userIds.map((id: number) => findUsername(id))}</span>
                </div>`;
      },
      className: 'echarts-tooltip-diy',
    },

    series: [
      generateSeries(
        t("commons.totalRequestsCount"),
        '#3469FF',
        '#E8F3FF'
      ),
    ],

    toolbox: {
      feature: {
        myDataZoom: {
          show: true,
          title: "DataZoom",
          icon: 'path://M0,0H12V2H0V0ZM0,14H12V16H0V14ZM0,6H12V8H0V6ZM0,10H12V12H0V10Z',
          onclick: () =>  {
            showDataZoom.value = !showDataZoom.value;
          }
        },
        restore: {},
        saveAsImage: {}
      }
    },
    dataZoom: dataZoomOption.value,
    // brush: {
    //   xAxisIndex: 0,
    //   throttleDelay: 300,
    //   brushType: 'lineX',
    //   brushMode: 'single',
    //   rangeMode: ['percent', 'percent'],
    //   outOfBrush: {
    //     colorAlpha: 0.1
    //   },
    // },
  }
})

watchEffect(() => {
  // console.log('props', props.requestCounts);
  // console.log('xAxis', xAxis.value);
  // console.log('totalRequestsCountData', totalRequestsCountData.value);
  // console.log('datasetSource', datasetSource.value);
  // console.log('users', props.users)
  console.log('option', option.value);
});
</script>
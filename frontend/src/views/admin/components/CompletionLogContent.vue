<template>
  <div class="w-full">
    <div class="mb-4 mt-1 ml-1 flex flex-row justify-between space-x-2">
      <n-button circle @click="refreshData()">
        <template #icon>
          <n-icon>
            <RefreshFilled />
          </n-icon>
        </template>
      </n-button>
      <div class="flex flex-wrap flex-row sm:space-x-3">
        <div class="option-item">
          <n-text>{{ t('commons.timeRange') }}</n-text>
          <n-date-picker v-model:value="range" size="small" class="w-80" type="daterange" clearable />
          <n-button-group size="small" round>
            <n-button @click="range = [Date.now() - 7 * 24 * 60 * 60 * 1000, Date.now()]">
              7d
            </n-button>
            <n-button @click="range = [Date.now() - 30 * 24 * 60 * 60 * 1000, Date.now()]">
              30d
            </n-button>
          </n-button-group>
        </div>
        <div class="option-item">
          <n-text>{{ t('commons.limit') }}</n-text>
          <n-input-number
            v-model:value="limit"
            size="small"
            class="w-27"
            :min="100"
            :max="100000"
            :step="100"
          />
        </div>
      </div>
    </div>
    <n-card class="my-4" :content-style="{ padding: '0px' }" :header-style="{ paddingBottom: 0 }">
      <UserUsageChart class="my-4" :loading="loading" :ask-logs="data" :users="userInfo" />
    </n-card>
    <div>
      <n-data-table
        size="small"
        :columns="columns"
        :data="data"
        :bordered="true"
        :pagination="{
          showSizePicker: true,
          pageSizes: [10, 20, 40, 100],
        }"
        :row-key="rowKey"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { RefreshFilled } from '@vicons/material';
import type { DataTableColumns } from 'naive-ui';
import { NButton, NEllipsis, NIcon, NTooltip } from 'naive-ui';
import { computed, h, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { getCompletionLogsApi } from '@/api/logs';
import { getAllUserApi } from '@/api/user';
import { AskLogDocument, UserReadAdmin } from '@/types/schema';
import { getChatModelNameTrans } from '@/utils/chat';
import { getDateStringSorter } from '@/utils/table';
import { parseTimeString } from '@/utils/time';
import { Message } from '@/utils/tips';

import UserUsageChart from './charts/UserUsageChart.vue';

const { t } = useI18n();
const router = useRouter();
const data = ref<AskLogDocument[]>([]);
const loading = ref(true);

const userInfo = ref<UserReadAdmin[] | undefined>(undefined);
const rowKey = (row: AskLogDocument) => row._id;

const range = ref<[number, number] | null>();
const startTime = computed<string | undefined>(() => {
  if (!range.value) return undefined;
  return new Date(range.value[0]).toISOString();
});
const endTime = computed<string | undefined>(() => {
  if (!range.value) return undefined;
  return new Date(range.value[1] + 24 * 60 * 60 * 1000).toISOString();
});

const limit = ref(1000);

const refreshData = (showTip = true) => {
  loading.value = true;
  getCompletionLogsApi(startTime.value, endTime.value, limit.value)
    .then((res) => {
      data.value = res.data;
      if (showTip) Message.success(t('tips.refreshed'));
    })
    .finally(() => {
      loading.value = false;
    });
};

const userIdFilterOptions = computed(() => {
  return userInfo.value?.map((user) => {
    return {
      label: user.username,
      value: user.id,
    };
  });
});

const columns = computed<DataTableColumns<AskLogDocument>>(() => [
  {
    title: t('commons.time'),
    key: 'time',
    width: 80,
    defaultSortOrder: 'descend',
    sorter: getDateStringSorter<AskLogDocument>('time'),
    render: (row) => {
      if (!row.time) return '';
      return h(
        NTooltip,
        { trigger: 'hover' },
        {
          trigger: () => parseTimeString(row.time!),
          default: () => row.time,
        }
      );
    },
  },
  {
    title: t('labels.source'),
    key: 'type',
    width: 50,
    render: (row) => {
      return t(`sources_short.${row.meta.source}`);
    },
  },
  {
    title: t('commons.modelName'),
    key: 'current_model',
    width: 80,
    render(row) {
      return row.meta.model ? getChatModelNameTrans(row.meta.model) : t('commons.unknown');
    },
    sorter: 'default',
  },
  {
    title: t('labels.conversation_id'),
    key: 'conversation_id',
    width: 80,
    ellipsis: true,
    render: (row) => {
      if (!row.conversation_id) return t('commons.empty');
      return h(
        NButton,
        {
          text: true,
          tag: 'a',
          href: router.resolve({
            name: 'conversationHistory',
            params: { conversation_id: row.conversation_id },
          }).href,
          target: '_blank',
        },
        {
          default: () => h(NEllipsis, { style: 'max-width: 400px' }, { default: () => row.conversation_id }),
        }
      );
    },
  },
  {
    title: t('commons.user'),
    key: 'user_id',
    width: 60,
    render: (row) => {
      // return userInfo.value?.find((user) => user.id === row.user_id)?.username || t('commons.empty');
      const user = userInfo.value?.find((user) => user.id === row.user_id);
      return h(
        NTooltip,
        { trigger: 'hover' },
        {
          trigger: () => user?.username || t('commons.unknown'),
          default: () => {
            let result = user?.nickname || user?.username || `${row.user_id}`;
            if (user?.remark) {
              result += ` (${user.remark})`;
            }
            return result;
          },
        }
      );
    },
    ellipsis: {
      tooltip: true,
    },
    filterOptions: userIdFilterOptions.value,
    defaultFilterOptionValues: userInfo.value?.map((user) => user.id),
    filter: (value, row) => {
      return row.user_id === value;
    },
  },
  {
    title: t('labels.ask_time'),
    key: 'ask_time',
    width: 50,
    render(row) {
      return `${row.ask_time}s`;
    },
    sorter: (a, b) => {
      return (a.ask_time || 0) - (b.ask_time || 0);
    },
  },
  {
    title: t('labels.queueing_time'),
    key: 'queueing_time',
    width: 50,
    render(row) {
      return `${row.queueing_time}s`;
    },
    sorter: (a, b) => {
      return (a.queueing_time || 0) - (b.queueing_time || 0);
    },
  },
]);

getAllUserApi().then((res) => {
  userInfo.value = res.data;
});

refreshData(false);

watch(range, () => {
  // if (!startTime.value || !endTime.value) return;
  refreshData();
});

watch(limit, () => {
  refreshData();
});
</script>

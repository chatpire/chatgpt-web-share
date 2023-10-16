<template>
  <n-card>
    <template #header>
      <div class="flex flex-row space-x-2">
        <n-text>{{ t('commons.serverOverview') }}</n-text>
        <n-button text @click="refresh">
          <template #icon>
            <n-icon :class="{ spin: isSpinning }">
              <RefreshFilled />
            </n-icon>
          </template>
        </n-button>
      </div>
    </template>
    <div class="grid grid-cols-3 md:grid-cols-6 gap-4">
      <n-statistic v-for="item in statistics" :key="item.label" :label="item.label" :value="item.value">
        <template v-if="item.prefixIcon" #prefix>
          <n-icon :component="item.prefixIcon" />
        </template>
        <template #suffix>
          <n-text>
            {{ item.suffix }}
          </n-text>
        </template>
      </n-statistic>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { RefreshFilled } from '@vicons/material';
import { computed, nextTick, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { CommonStatusSchema, SystemInfo } from '@/types/schema';
const { t } = useI18n();

const props = defineProps<{
  systemInfo?: SystemInfo;
  serverStatus?: CommonStatusSchema;
}>();

const emits = defineEmits<{
  (e: 'refresh'): void;
}>();

const isSpinning = ref(false);

const refresh = async () => {
  isSpinning.value = true;

  // Trigger the animation and wait for the next DOM update
  await nextTick();

  // After the animation plays, reset the spinning state
  setTimeout(() => {
    isSpinning.value = false;
  }, 1000); // Adjust the timeout to match the animation duration

  emits('refresh');
};

function hoursSince(timestamp?: number) {
  if (!timestamp) {
    return 'N/A';
  }
  const now = new Date();
  const diff = now.getTime() - timestamp * 1000; // 将 Unix 时间戳转换为毫秒
  const hours = diff / 1000 / 3600; // 将毫秒转换为小时
  return hours.toFixed(1); // 保留一位小数
}

const statistics = computed(() => {
  return [
    {
      label: t('commons.userCountAndOnlineCount'),
      value: props.serverStatus?.active_user_in_5m,
      prefixIcon: null,
      suffix: `/ ${props.systemInfo?.total_user_count}`,
    },
    {
      label: t('commons.conversationCount'),
      value: props.systemInfo?.valid_conversation_count,
      prefixIcon: null,
      suffix: `/ ${props.systemInfo?.total_conversation_count}`,
    },
    {
      label: t('labels.gpt4_count_in_3_hours'),
      value: props.serverStatus?.gpt4_count_in_3_hours,
      prefixIcon: null,
      suffix: '',
    },
    {
      label: t('commons.chatbotStatus'),
      value: props.serverStatus?.is_chatbot_busy ? t('commons.askingChatStatus') : t('commons.idlingChatStatus'),
      prefixIcon: null,
    },
    {
      label: t('commons.chatbotWaitingCount'),
      value: props.serverStatus?.chatbot_waiting_count,
      prefixIcon: null,
    },
    {
      label: t('commons.startUpDuration'),
      value: hoursSince(props.systemInfo?.startup_time),
      prefixIcon: null,
      suffix: ' h',
    },
  ];
});
</script>

<style scoped>
@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.spin {
  animation: spin 1s ease-in-out;
}
</style>

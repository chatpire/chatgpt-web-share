<template>
  <n-card :title="t('commons.serverOverview')">
    <div class="grid grid-cols-3 md:grid-cols-5 gap-4">
      <n-statistic v-for="item in statistics" :key="item.label" :label="item.label" :value="item.value">
        <template #prefix v-if="item.prefixIcon">
          <n-icon :component="item.prefixIcon"></n-icon>
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
import { getSystemInfoApi } from '@/api/system';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { ServerStatusSchema, SystemInfo } from '@/types/schema';
const { t } = useI18n();

const props = defineProps<{
  systemInfo?: SystemInfo;
  serverStatus?: ServerStatusSchema;
}>();

function hoursSince(timestamp?: number) {
  if (!timestamp) {
    return 'N/A'
  }
  const now = new Date()
  const diff = now.getTime() - timestamp * 1000 // 将 Unix 时间戳转换为毫秒
  const hours = diff / 1000 / 3600 // 将毫秒转换为小时
  return hours.toFixed(1) // 保留一位小数
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
      suffix: ' h'
    },
  ];
})

</script>

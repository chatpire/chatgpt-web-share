<template>
  <n-card :title="t('commons.serverOverview')">
    <div class="grid grid-cols-4 gap-4">
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
  ];
})

</script>

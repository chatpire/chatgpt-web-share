<template>
  <HistoryContent
    :conversation-id="conversationId"
    :fullscreen="false"
    :show-tips="false"
    :extra-messages="[]"
    :loading="loading"
  />
</template>

<script setup lang="ts">
import { useThemeVars } from 'naive-ui';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRoute, useRouter } from 'vue-router';

import { useConversationStore } from '@/store';
import { getChatModelNameTrans } from '@/utils/chat';
import { getMessageListFromHistory } from '@/utils/conversation';

import HistoryContent from './components/HistoryContent.vue';

const conversationStore = useConversationStore();

const themeVars = useThemeVars();
const { t } = useI18n();
const route = useRoute();
const router = useRouter();
const conversationId = route.params.conversation_id as string;

const loading = ref(true);

conversationStore
  .fetchConversationHistory(conversationId)
  .then(() => {
    // console.log(conversationStore.conversationDetailMap);
  })
  .catch((err: any) => {
    console.log(err);
    router.push({ name: '404' }).then();
  })
  .finally(() => {
    loading.value = false;
  });
</script>

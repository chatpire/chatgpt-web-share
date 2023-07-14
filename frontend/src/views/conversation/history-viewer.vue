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
import { ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';

import { getConversationHistoryFromCacheApi } from '@/api/conv';
import { useConversationStore } from '@/store';

import HistoryContent from './components/HistoryContent.vue';

const conversationStore = useConversationStore();

const route = useRoute();
const router = useRouter();
const conversationId = route.params.conversation_id as string;

const loading = ref(true);

conversationStore
  .fetchConversationHistoryFromCache(conversationId, true)
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

<template>
    <HistoryContent :messages="messages" :fullscreen="false" :show-tips="false" :append-messages="[]" :loading="loading" />
</template>

<script setup lang="ts">
import HistoryContent from './components/HistoryContent.vue';
import { useRoute, useRouter } from 'vue-router';
import { getConvMessageListFromId } from "@/utils/conversation";
import { useConversationStore } from "@/store";
import { ref, computed } from 'vue';

const conversationStore = useConversationStore();

const route = useRoute();
const router = useRouter();
const conversationId = route.params.conversation_id as string;

const loading = ref(true);

conversationStore.fetchConversationHistory(conversationId).then(() => {
    // console.log(conversationStore.conversationDetailMap);
}).catch((err: any) => {
    console.log(err);
    router.push({ name: '404' }).then();
}).finally(() => {
    loading.value = false;
});

const messages = computed(() => {
    return getConvMessageListFromId(conversationId);
})

</script>
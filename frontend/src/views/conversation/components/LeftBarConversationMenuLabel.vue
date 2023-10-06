<!-- not used -->

<template>
  <div class="h-full flex items-center" @mouseover="unsetTransparent" @mouseleave="setTransparent">
    <ChatGPTAvatar :alpha="alpha" :size="20" :model="props.conversation.current_model" />

    <n-ellipsis class="w-full">
      {{ conversation.title || 'New chat' }}
    </n-ellipsis>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import ChatGPTAvatar from '@/components/ChatGPTAvatar.vue';
import { BaseConversationSchema } from '@/types/schema';

// const color = ref<string | undefined>(undefined);
const alpha = ref<number | undefined>(30);

const props = defineProps<{
  conversation: BaseConversationSchema;
}>();

const setTransparent = () => {
  alpha.value = 30;
};

const unsetTransparent = () => {
  alpha.value = undefined;
};
</script>

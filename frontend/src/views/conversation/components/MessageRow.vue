<template>
  <div :class="['flex flex-row py-4 px-4 max-w-full', props.message.author_role == 'user' ? 'bg-white' : 'bg-green-50']">
    <div class="min-w-16 text-right">
      <n-text class="inline-block mt-4">{{ props.message.author_role == 'user' ? 'User' : 'ChatGPT' }}</n-text>
    </div>
    <div class="mx-4 w-full">
      <div class="w-full" v-html="renderedContent"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ChatMessage } from '@/types/custom';
import md from "@/utils/markdown";

const props = defineProps<{
  message: ChatMessage;
}>()

const renderedContent = computed(() => {
  const result = md.render(props.message.message || '');
  return result
});
</script>

<style>
code {
  max-width: 600px;
}

ol,
ul {
  padding-left: 16px;
}
</style>
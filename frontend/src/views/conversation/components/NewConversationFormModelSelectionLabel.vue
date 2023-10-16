<template>
  <div class="flex flex-row space-x-2">
    <div class="flex items-center">
      <ChatGPTAvatar :size="20" :model="props.model" />
    </div>
    <div class="flex items-center">
      <div class="text-sm font-medium">
        {{ t('models.' + props.model) }}
      </div>
      <!-- <div class="text-xs text-gray-400">
        {{ t(`modelDescriptions.${props.source}.${props.model}`) }}
      </div> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import ChatGPTAvatar from '@/components/ChatGPTAvatar.vue';
import { i18n } from '@/i18n';
const t = i18n.global.t as any;

const props = defineProps<{
  source: 'openai_web' | 'openai_api' | string;
  model: string;
}>();
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
</style>

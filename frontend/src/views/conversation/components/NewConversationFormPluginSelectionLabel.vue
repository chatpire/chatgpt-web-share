<template>
  <div class="flex flex-row space-x-2">
    <div class="flex items-center">
      <n-avatar :size="24" :src="props.plugin?.manifest?.logo_url" />
    </div>
    <div class="flex flex-col">
      <div class="text-sm font-medium">
        {{ props.plugin?.manifest?.name_for_human }}
      </div>
      <div class="text-xs text-gray-400">
        {{ props.plugin?.manifest?.description_for_human }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// import { watchEffect } from 'vue';

import { OpenaiChatPlugin } from '@/types/schema';

const props = defineProps<{
  plugin?: OpenaiChatPlugin;
}>();

// watchEffect(() => {
//   console.log(props.plugin);
// });
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
}
</style>

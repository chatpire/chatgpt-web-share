<template>
  <div class="inline-flex flex-row space-x-2">
    <n-tooltip v-for="(val, key) of props.value" :key="key" trigger="hover">
      <template #trigger>
        <n-tag round>
          {{ val }}
          <template #avatar>
            <ChatGPTAvatar :color="getChatModelColor(key)" />
          </template>
        </n-tag>
      </template>
      {{ $t(`models.${key}`) }}
    </n-tooltip>
  </div>
</template>

<script lang="ts" setup>
import ChatGPTAvatar from '@/components/ChatGPTAvatar.vue';
import { getChatModelColor } from '@/utils/chat';

const props = defineProps<{
  value: Record<string, string>;
}>();
</script>
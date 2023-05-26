<template>
  <div class="flex flex-row flex-wrap gap-y-1 items-start gap-x-2">
    <n-tooltip v-for="(val, key) of props.value" :key="key" trigger="hover">
      <template #trigger>
        <n-tag round>
          {{ val }}
          <template #avatar>
            <ChatGPTAvatar :icon-style="getChatModelIconStyle(key)" :color="getChatModelColor(key)" />
          </template>
        </n-tag>
      </template>
      {{ t(`models.${key}`) }}
    </n-tooltip>
  </div>
</template>

<script lang="ts" setup>
import ChatGPTAvatar from '@/components/ChatGPTAvatar.vue';
import { i18n } from '@/i18n';
import { getChatModelColor, getChatModelIconStyle } from '@/utils/chat';

const t = i18n.global.t as any;
const props = defineProps<{
  value: Record<string, string>;
}>();
</script>

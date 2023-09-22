<template>
  <n-collapse class="rounded-2 border-1 border-solid border-gray-200 w-full max-w-60 p-3">
    <template #arrow>
      <n-icon><AttachFileFilled /></n-icon>
    </template>
    <n-collapse-item :title="$t('commons.viewAttachments', [attachments.length])" name="1">
      <n-list hoverable>
        <n-list-item v-for="(item, index) of attachments" :key="index">
          <div class="flex flex-row justify-between">
            <span class="font-bold">{{ item.name }}</span>
            <span>size: {{ sizeToHumanReadable(item.size || 0) }}</span>
          </div>
        </n-list-item>
      </n-list> 
    </n-collapse-item>
  </n-collapse>
</template>

<script setup lang="ts">
import {AttachFileFilled} from '@vicons/material';
import { computed } from 'vue';

import { OpenaiWebChatMessageMetadataAttachment } from '@/types/schema';

// metadata
const props = defineProps<{
  attachments: OpenaiWebChatMessageMetadataAttachment[];
}>();

const attachments = computed(() => {
  return props.attachments;
});

function sizeToHumanReadable(size: number) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
  let unitIndex = 0;
  while (size > 1024) {
    size /= 1024;
    unitIndex++;
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`;
}

</script>

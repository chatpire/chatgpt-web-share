<template>
  <div class="mr-4 w-full max-w-100 mt-2 mb-1">
    <n-card :content-style="{ padding: 0 }">
      <n-collapse>
        <template #arrow>
          <n-icon><AttachFileFilled /></n-icon>
        </template>
        <n-collapse-item class="p-4!" :title="$t('commons.viewAttachments', [attachments.length])" name="1">
          <n-list hoverable>
            <n-list-item v-for="(item, index) of attachments" :key="index">
              <div class="flex flex-row justify-between">
                <span class="font-bold"><n-ellipsis style="max-width: 200px">{{ item.name }}</n-ellipsis></span>
                <span>{{ sizeToHumanReadable(item.size || 0) }}</span>
              </div>
            </n-list-item>
          </n-list>
        </n-collapse-item>
      </n-collapse>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { AttachFileFilled } from '@vicons/material';
import { computed } from 'vue';

import { OpenaiWebChatMessageMetadataAttachment } from '@/types/schema';
import { sizeToHumanReadable } from '@/utils/media';

// metadata
const props = defineProps<{
  attachments: OpenaiWebChatMessageMetadataAttachment[];
}>();

const attachments = computed(() => {
  return props.attachments;
});
</script>

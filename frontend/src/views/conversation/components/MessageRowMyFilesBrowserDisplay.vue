<template>
  <div class="flex flex-col items-start my-2">
    <div
      class="flex items-center text-xs rounded p-3 text-gray-900 bg-gray-100 max-w-full box-border"
      @click="handleExpand"
    >
      <n-ellipsis class="flex items-center gap-3">
        {{ $t('commons.myFileBrowser') }}
      </n-ellipsis>
      <div class="ml-12 flex items-center gap-2" role="button">
        <n-icon :size="16" :component="expandContent ? KeyboardArrowUpRound : KeyboardArrowDownRound" />
      </div>
    </div>
    <div v-show="expandContent" class="my-3 flex max-w-full flex-col gap-3">
      <div v-if="code?.length" class="bg-black rounded-md w-full text-xs text-white/80">
        <div
          class="flex items-center relative text-gray-200 bg-gray-800 px-4 py-2 text-xs font-sans justify-between rounded-t-md"
        >
          {{ $t('commons.executeCode') }}
        </div>
        <div class="p-4 max-h-100 overflow-y-auto">
          <code class="!whitespace-pre-wrap">
            {{ code }}
          </code>
        </div>
      </div>
      <div v-if="content?.length" class="bg-black rounded-md w-full text-xs text-white/80">
        <div
          class="flex items-center relative text-gray-200 bg-gray-800 px-4 py-2 text-xs font-sans justify-between rounded-t-md"
        >
          {{ $t('commons.content') }}
        </div>
        <div class="p-4 max-h-80 overflow-y-auto">
          <code class="!whitespace-pre-wrap">
            {{ content }}
          </code>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { InformationCircleOutline } from '@vicons/ionicons5';
import { KeyboardArrowDownRound, KeyboardArrowUpRound } from '@vicons/material';
import { computed, ref } from 'vue';

import {
  BaseChatMessage,
  OpenaiWebChatMessage,
  OpenaiWebChatMessageCodeContent,
  OpenaiWebChatMessageTetherBrowsingDisplayContent,
} from '@/types/schema';

const props = defineProps<{
  messages: BaseChatMessage[];
}>();

const expandContent = ref(false);

const code = computed(() => {
  if (!props.messages || props.messages.length === 0) return '';
  if (props.messages[0].content?.content_type !== 'code') {
    console.error('MessageRowMyFilesBrowserDisplay: message[0] content is not code', props.messages);
    return '';
  }
  const content = props.messages[0].content as OpenaiWebChatMessageCodeContent;
  return content.text;
});

const content = computed(() => {
  if (!props.messages || props.messages.length < 2) return '';
  if (props.messages[1].content?.content_type !== 'tether_browsing_display') {
    console.error('MessageRowMyFilesBrowserDisplay: message[1] content is not tether_browsing_display', props.messages);
    return '';
  }
  const content = props.messages[1].content as OpenaiWebChatMessageTetherBrowsingDisplayContent;
  return content.result;
});

function handleExpand() {
  expandContent.value = !expandContent.value;
}
</script>

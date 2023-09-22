<template>
  <div class="flex flex-col items-start my-2">
    <div class="flex items-center text-xs rounded p-3 text-gray-900 bg-gray-100" @click="handleExpand">
      <div>
        <div class="flex items-center gap-3">
          <div>
            {{ $t('commons.useCodeInterpreter') }}
          </div>
        </div>
      </div>
      <div class="ml-12 flex items-center gap-2" role="button">
        <n-icon :size="16" :component="expandContent ? KeyboardArrowUpRound : KeyboardArrowDownRound" />
      </div>
    </div>
    <div v-show="expandContent" class="my-3 flex w-full flex-col gap-3">
      <div class="code-border" v-html="renderedCodeContent" />
      <div v-if="result != null" class="rounded-md bg-black p-4 text-xs">
        <div class="mb-1 text-gray-400">
          RESULT
        </div>
        <div
          class="scrollbar-thin scrollbar-thumb-gray-400 scrollbar-track-gray-700 prose flex max-h-64 flex-col-reverse overflow-auto text-white"
        >
          <pre class="shrink-0">{{ result }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { KeyboardArrowDownRound, KeyboardArrowUpRound } from '@vicons/material';
import { computed, ref } from 'vue';

import { useAppStore } from '@/store';
import {
  BaseChatMessage,
  OpenaiWebChatMessage,
  OpenaiWebChatMessageCodeContent,
  OpenaiWebChatMessageExecutionOutputContent,
  OpenaiWebChatMessageMetadata,
} from '@/types/schema';
import md from '@/utils/markdown';

import { processPreTags } from '../utils/codeblock';

const appStore = useAppStore();
const props = defineProps<{
  messages: BaseChatMessage[];
}>();

const code = computed(() => {
  if (props.messages.length === 0) return null;
  const message = props.messages[0] as OpenaiWebChatMessage;
  if (message.content?.content_type !== 'code') {
    console.error('MessageRowCodeDisplay: message content type is not code', message);
  }
  const content = message.content as OpenaiWebChatMessageCodeContent;
  return content.text;
});

const result = computed(() => {
  if (props.messages.length < 2) return null;
  const message = props.messages[1] as OpenaiWebChatMessage;
  if (message.content?.content_type !== 'execution_output') {
    console.error('MessageRowCodeDisplay: message content type is not execution_output', message);
  }
  const content = message.content as OpenaiWebChatMessageExecutionOutputContent;
  const metadata = message.metadata as OpenaiWebChatMessageMetadata;
  // if (metadata.aggregate_result == null)
  return content.text;
});

const renderedCodeContent = computed(() => {
  const result = md.render(`
\`\`\`python
${code.value}
\`\`\`
  `);
  return processPreTags(result, appStore.preference.codeAutoWrap);
});

const expandContent = ref(true);

function handleExpand() {
  expandContent.value = !expandContent.value;
}
</script>

<style>
.code-border > pre {
  @apply border-blue-500 border-0 border-l-4 border-solid;
}

</style>
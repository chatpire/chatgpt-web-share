<template>
  <div class="flex flex-col items-start mt-3">
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
    <div v-show="expandContent" class="my-2 flex flex-col w-full gap-3">
      <!-- code -->
      <div ref="codeRef" class="code-border" v-html="renderedCodeContent" />
      <!-- result -->
      <div v-if="result != null" class="rounded-md bg-black p-4 text-xs code-result">
        <div class="mb-1 text-gray-400">
          RESULT
        </div>
        <div class="max-h-64 overflow-auto whitespace-pre-line font-mono text-white">
          {{ result }}
        </div>
        <!-- image -->
      </div>
      <div v-if="imageDownloadUrls.length > 0" class="mt-2">
        <n-image-group>
          <div v-for="url of imageDownloadUrls" :key="url" class="max-w-80">
            <n-image :src="url" :height="200" />
          </div>
        </n-image-group>
      </div>
    </div>
  </div>
</template>
<script setup lang="ts">
import { KeyboardArrowDownRound, KeyboardArrowUpRound } from '@vicons/material';
import { computed, onMounted, ref, watch } from 'vue';

import { getFileDownloadUrlApi } from '@/api/conv';
import { useAppStore } from '@/store';
import {
  BaseChatMessage,
  OpenaiWebChatMessage,
  OpenaiWebChatMessageCodeContent,
  OpenaiWebChatMessageExecutionOutputContent,
  OpenaiWebChatMessageMetadata,
} from '@/types/schema';
import md from '@/utils/markdown';
import { Message } from '@/utils/tips';

import { bindOnclick, processPreTags } from '../utils/codeblock';
import { getImageDownloadUrlFromFileServiceSchemaUrl } from '../utils/message';

const appStore = useAppStore();
const props = defineProps<{
  messages: BaseChatMessage[];
}>();

const codeRef = ref<HTMLDivElement>();

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
  // if (metadata.aggregate_result == null)
  let text = content.text?.replace('<<ImageDisplayed>>', '').trim();
  if (text == null || text === '') return null;
  return text;
});

const renderedCodeContent = computed(() => {
  const result = md.render(`
\`\`\`python
${code.value}
\`\`\`
  `);
  return processPreTags(result, appStore.preference.codeAutoWrap);
});

const imageDownloadUrls = ref<string[]>([]);

async function getImageDownloadUrls() {
  const message = props.messages[1] as OpenaiWebChatMessage;
  if (!message) return;
  if (message.content?.content_type !== 'execution_output') {
    console.error('MessageRowCodeDisplay: message content type is not execution_output', message);
  }
  const metadata = message.metadata as OpenaiWebChatMessageMetadata;
  if (metadata.aggregate_result == null) return [];
  const aggregateMessages = metadata.aggregate_result.messages;
  if (!aggregateMessages) return [];
  const imageUrls = aggregateMessages
    .filter((message) => message.message_type === 'image')
    .map((message) => message.image_url); // starts with file-service://
  const result = [];
  for (const url of imageUrls) {
    const downloadUrl = await getImageDownloadUrlFromFileServiceSchemaUrl(url);
    if (downloadUrl == null) {
      Message.error(`Failed to get image download url for ${url}`);
      continue;
    }
    result.push(downloadUrl);
  }
  imageDownloadUrls.value = result;
}

const expandContent = ref(true);

function handleExpand() {
  expandContent.value = !expandContent.value;
}

let observer = null;
onMounted(() => {
  if (!codeRef.value) return;
  // eslint-disable-next-line no-undef
  const callback: MutationCallback = (mutations: MutationRecord[]) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        bindOnclick(codeRef);
      }
    }
  };

  observer = new MutationObserver(callback);
  observer.observe(codeRef.value, { subtree: true, childList: true });
  bindOnclick(codeRef);
});

getImageDownloadUrls().then();
</script>

<style>
.code-border > pre {
  @apply border-blue-500 border-0 border-l-4 border-solid;
}
</style>

<template>
  <div v-if="props.renderMarkdown" ref="contentRef" class="message-content w-full" v-html="renderedContent" />
  <div v-else ref="contentRef" class="message-content w-full whitespace-pre-wrap py-4">
    {{ renderedContent }}
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { useAppStore } from '@/store';
import { BaseChatMessage } from '@/types/schema';
import { getTextMessageContent } from '@/utils/chat';
import md from '@/utils/markdown';

import { bindOnclick, processPreTags } from '../utils/codeblock';

const appStore = useAppStore();
const contentRef = ref<HTMLDivElement>();

const props = defineProps<{
  messages: BaseChatMessage[],
  renderMarkdown: boolean
}>();

const content = computed(() => {
  return getTextMessageContent(props.messages);
});

const renderedContent = computed(() => {
  if (!props.renderMarkdown) {
    return content.value;
  }
  const result = md.render(content.value || '');
  return processPreTags(result, appStore.preference.codeAutoWrap);
});

let observer = null;
onMounted(() => {
  if (!contentRef.value) return;
  // eslint-disable-next-line no-undef
  const callback: MutationCallback = (mutations: MutationRecord[]) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        bindOnclick(contentRef);
      }
    }
  };
  observer = new MutationObserver(callback);
  observer.observe(contentRef.value, { subtree: true, childList: true });
  bindOnclick(contentRef);
});
</script>
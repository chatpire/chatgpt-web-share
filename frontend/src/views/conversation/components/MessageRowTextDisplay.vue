<template>
  <div v-if="props.renderMarkdown" ref="contentRef" class="message-content w-full" v-html="renderedContent" />
  <div v-else class="message-content w-full whitespace-pre-wrap py-4">
    {{ renderedContent }}
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';

import { useAppStore } from '@/store';
import { BaseChatMessage, OpenaiWebChatMessageMetadata, OpenaiWebChatMessageMetadataCiteData } from '@/types/schema';
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

function htmlToElement(html: string) {
  var template = document.createElement('template');
  template.innerHTML = html.trim();
  return template.content.firstChild;
}

function processCitations() {
  const citationEls = contentRef.value!.querySelectorAll('span.browsing-citation');
  const citationUrls = [] as string[];
  console.log(citationEls);
  citationEls.forEach(el => {
    let metadata = JSON.parse(decodeURIComponent(el.getAttribute('data-citation') || '')) as OpenaiWebChatMessageMetadataCiteData;
    console.log(metadata);
    if (!metadata) return;
    let citationIndex = 0;
    if (citationUrls.includes(metadata.url!)) {
      citationIndex = citationUrls.indexOf(metadata.url!) + 1;
    } else {
      citationUrls.push(metadata.url!);
      citationIndex = citationUrls.length;
    }
    const newEl = htmlToElement(`<a href="${metadata.url!}" target="_blank" rel="noreferrer" class="px-0.5 text-green-600 !no-underline"><sup>${citationIndex}</sup></a>`);
    if (newEl) el.replaceWith(newEl);
  });
}

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
    processCitations();
  };
  observer = new MutationObserver(callback);
  observer.observe(contentRef.value, { subtree: true, childList: true });
  bindOnclick(contentRef);
  processCitations();
});

</script>
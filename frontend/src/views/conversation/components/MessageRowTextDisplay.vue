<template>
  <div v-if="props.renderMarkdown" ref="contentRef" class="message-content w-full" v-html="renderedContent" />
  <div v-else class="message-content w-full whitespace-pre-wrap py-4">
    {{ renderedContent }}
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { getInterpreterSandboxFileDownloadUrlApi } from '@/api/conv';
import { useAppStore } from '@/store';
import { BaseChatMessage, OpenaiWebChatMessageMetadataCiteData } from '@/types/schema';
import { getTextMessageContent } from '@/utils/chat';
import md from '@/utils/markdown';
import { Dialog } from '@/utils/tips';

import { bindOnclick, processPreTags } from '../utils/codeblock';

const appStore = useAppStore();
const contentRef = ref<HTMLDivElement>();
const { t } = useI18n();

const props = defineProps<{
  conversationId: string;
  messages: BaseChatMessage[];
  renderMarkdown: boolean;
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
  citationEls.forEach((el) => {
    let metadata = JSON.parse(
      decodeURIComponent(el.getAttribute('data-citation') || '')
    ) as OpenaiWebChatMessageMetadataCiteData;
    if (!metadata) return;
    let citationIndex = 0;
    if (citationUrls.includes(metadata.url!)) {
      citationIndex = citationUrls.indexOf(metadata.url!) + 1;
    } else {
      citationUrls.push(metadata.url!);
      citationIndex = citationUrls.length;
    }
    const newEl = htmlToElement(
      `<a href="${metadata.url!}" target="_blank" rel="noreferrer" class="px-0.5 text-green-600 !no-underline"><sup>${citationIndex}</sup></a>`
    );
    if (newEl) el.replaceWith(newEl);
  });
}

function processSandboxLinks() {
  const sandboxLinks = contentRef.value!.querySelectorAll('a[href^="sandbox:"]');

  sandboxLinks.forEach((link) => {
    link.classList.add('sandbox');
    const hrefValue = link.getAttribute('href');
    const path = hrefValue?.replace('sandbox:', '');
    link.setAttribute('data-path', path || '');
    link.addEventListener('click', handleSandboxLinkClick);
  });
}

function findMessageIdOfSandboxFile(sandboxPath: string) {
  const messages = props.messages;
  for (let i = 0; i < messages.length; i++) {
    const message = messages[i];
    const content = getTextMessageContent([message]);
    console.log(`search ${sandboxPath} in ${content}`);
    if (content.includes(sandboxPath)) {
      return message.id;
    }
  }
  return null;
}

function handleSandboxLinkClick(event: Event) {
  const target = event.target as HTMLElement;

  if (target && target.matches('a.sandbox')) {
    event.preventDefault();

    // 设置元素禁止点击
    target.style.pointerEvents = 'none';

    const path = target.getAttribute('data-path');
    const messageId = findMessageIdOfSandboxFile(path!);
    if (!path) return;
    if (!messageId) return;

    getInterpreterSandboxFileDownloadUrlApi(props.conversationId, messageId, path)
      .then((response) => {
        const url = response.data;
        window.open(url, '_blank');
      })
      .catch((e) => {
        console.error(e);
        if (e.message == 'errors.resourceNotFound') {
          Dialog.warning({
            content: t('tips.sandboxFileNotFound', [path]),
          });
        } else {
          Dialog.error({
            title: 'Error',
            content: t('tips.sandboxFileDownloadError'),
          });
        }
      }).finally(() => {
        target.style.pointerEvents = 'auto';
      });
  }
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
  processSandboxLinks();
});
</script>

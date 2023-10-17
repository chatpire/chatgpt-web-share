<template>
  <div class="mt-3">
    <n-image-group>
      <div class="max-w-sm sm:max-w-lg lg:max-w-1/2 grid gap-4 grid-cols-2">
        <n-image
          v-for="image in imageInfos"
          :key="image.url"
          class="w-full h-auto overflow-hidden rounded-md"
          :src="image.url"
          lazy
          object-fit="cover"
          :img-props="{
            alt: 'Uploaded Image',
            class: 'max-w-full transition-opacity duration-300 opacity-100 object-cover',
          }"
        >
          <template #placeholder>
            <n-card>
              <div class="w-full h-full flex items-center justify-center content-center">
                <n-spin size="small" />
              </div>
            </n-card>
          </template>
        </n-image>
      </div>
    </n-image-group>
  </div>
  <div v-if="props.renderMarkdown" ref="contentRef" class="message-content w-full" v-html="renderedContent" />
  <div v-else class="message-content w-full whitespace-pre-wrap py-4">
    {{ renderedContent }}
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { useAppStore } from '@/store';
import { BaseChatMessage, OpenaiWebChatMessageMultimodalTextContentImagePart } from '@/types/schema';
import { dompurifyRenderedHtml, getContentRawText, getMultimodalContentImageParts } from '@/utils/chat';
import md from '@/utils/markdown';

import { bindOnclick, processPreTags } from '../utils/codeblock';
import { getImageDownloadUrlFromFileServiceSchemaUrl, processCitations, processSandboxLinks } from '../utils/message';

const appStore = useAppStore();
const contentRef = ref<HTMLDivElement>();
const { t } = useI18n();

const props = defineProps<{
  conversationId: string;
  messages: BaseChatMessage[];
  renderMarkdown: boolean;
}>();

const content = computed(() => {
  return getContentRawText(props.messages[0]);
});

const renderedContent = computed(() => {
  if (!props.renderMarkdown) {
    return content.value;
  }
  const result = dompurifyRenderedHtml(md.render(content.value || ''));
  return processPreTags(result, appStore.preference.codeAutoWrap);
});

type ImageInfo = {
  url: string;
  data: OpenaiWebChatMessageMultimodalTextContentImagePart;
};

const imageInfos = ref<ImageInfo[]>([]);

async function fetchImageUrls() {
  const result = [] as ImageInfo[];
  const parts = getMultimodalContentImageParts(props.messages[0]);
  for (const imagePart of parts) {
    const url = await getImageDownloadUrlFromFileServiceSchemaUrl(imagePart.asset_pointer);
    if (url) {
      result.push({
        data: imagePart,
        url,
      });
    }
  }
  imageInfos.value = result;
}

fetchImageUrls().then();

let observer = null;
onMounted(() => {
  if (!contentRef.value) return;
  // eslint-disable-next-line no-undef
  const callback: MutationCallback = (mutations: MutationRecord[]) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        bindOnclick(contentRef);
        processCitations(contentRef.value!);
        processSandboxLinks(contentRef.value!, props.conversationId, props.messages);
      }
    }
  };

  observer = new MutationObserver(callback);
  observer.observe(contentRef.value, { subtree: true, childList: true });
  bindOnclick(contentRef);
  processCitations(contentRef.value!);
  processSandboxLinks(contentRef.value!, props.conversationId, props.messages);
});
</script>

<style scoped>
img {
  overflow-clip-margin: 'content-box';
  overflow: 'clip';
  height: 'auto';
}
</style>

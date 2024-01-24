<template>
  <div class="mt-3">
    <!-- 单张图片 -->
    <n-image
      v-if="imageInfos.length == 1"
      class="max-w-sm sm:max-w-md lg:max-w-lg w-full h-auto overflow-hidden rounded-md"
      :src="imageInfos[0].url"
      lazy
      :width="imageInfos[0].data.width || 100"
      :height="imageInfos[0].data.height || 100"
      :img-props="{
        alt: 'Uploaded Image',
        class: 'max-w-full h-auto transition-opacity duration-300 opacity-100',
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

    <!-- 多张图片 -->
    <n-image-group v-else>
      <div v-if="imageInfos.length > 0" class="max-w-sm sm:max-w-md lg:max-w-lg grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4">
        <n-image
          v-for="image in imageInfos"
          :key="image.url"
          class="w-full h-auto aspect-square overflow-hidden rounded-md"
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
  if (props.messages.length > 1) {
    console.error('Multimodal text content should only have one message.');
  }
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

<template>
  <div class="pt-3 flex flex-col items-start">
    <div class="flex items-center text-xs rounded p-3 text-gray-900 bg-gray-100" @click="handleExpand">
      <div>
        <div class="flex items-center gap-2">
          <div>{{ $t('commons.browsingHistory') }}</div>
        </div>
      </div>
      <div class="ml-12 flex items-center gap-2" role="button">
        <n-icon :size="16" :component="expandContent ? KeyboardArrowUpRound : KeyboardArrowDownRound" />
      </div>
    </div>
    <div
      v-show="expandContent"
      class="max-w-full overflow-x-auto mt-3 flex flex-col gap-2 rounded bg-gray-100 p-3 text-gray-800 text-xs"
    >
      <div v-for="(action, i) in displayActions" :key="i" class="flex items-center gap-2 min-h-[24px]">
        <BrowsingIcon :name="action.type" :size="14" />
        <div v-if="action.type == 'search'">
          {{ $t('commons.search') }} Bing:
          <span class="font-medium">“<a :href="getSearchUrl(action.searchContent)" target="_blank" rel="noreferrer" class="text-green-600">{{
            action.searchContent
          }}</a>”</span>
        </div>
        <div v-else-if="action.type == 'click'">
          <div class="flex items-center gap-2">
            {{ $t('commons.click') }}:
            <div class="rounded border border-black/10 bg-white px-2 py-1">
              <a
                :href="getCiteUrl(action.clickIndex, action.citeMetadata) || '#'"
                target="_blank"
                rel="noreferrer"
                class="text-xs !no-underline text-black"
              >
                <div class="flex items-center gap-2">
                  <!-- <div class="flex shrink-0 items-center justify-center">
                    <img alt="Favicon" width="16" height="16" class="my-0" />
                  </div> -->
                  <div class="max-w-xs truncate">{{ getCiteTitle(action.clickIndex, action.citeMetadata) }}</div>
                  <div class="shrink-0">
                    <!-- external link -->
                    <BrowsingIcon name="external_link" />
                  </div>
                </div>
              </a>
            </div>
          </div>
        </div>
        <div v-else-if="action.type == 'scroll'">
          <div class="flex items-center gap-2">
            {{ $t('commons.scrolling_down') }}
          </div>
        </div>
        <div v-else-if="action.type == 'click_result'">
          {{ $t('commons.readingContent') }}
        </div>
        <div v-else-if="action.type == 'failed'" class="max-w-xs truncate">
          {{ $t('commons.error') }} : {{ getContentRawText(action.message) }}
        </div>
        <!-- <div v-else-if="action.type == 'quote'">
        {{ $t('commons.quoteContent') }}
        </div> -->
        <n-popover trigger="hover" placement="right">
          <template #trigger>
            <div class="text-gray-400 hover:text-blue-500 cursor-pointer" @click="showContent(action)">
              {{ $t('commons.detail') }}
            </div>
          </template>
          <div class="max-w-200 whitespace-pre-line">
            {{ getContentRawText(action.message) }}
          </div>
        </n-popover>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { KeyboardArrowDownRound, KeyboardArrowUpRound } from '@vicons/material';
import { NScrollbar } from 'naive-ui';
import { computed, h, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import BrowsingIcon from '@/components/BrowsingIcon.vue';
import { BaseChatMessage, OpenaiWebChatMessageMetadata } from '@/types/schema';
import { getContentRawText } from '@/utils/chat';
import { Dialog } from '@/utils/tips';

const { t } = useI18n();

const props = defineProps<{
  messages: BaseChatMessage[];
}>();

type BrowsingAction = {
  type: 'search' | 'click' | 'scroll' | 'go_back' | 'click_result' | 'quote' | 'quote_result' | 'failed';
  message: BaseChatMessage;
  searchContent?: string;
  clickIndex?: string;
  citeMetadata?: CiteMetadata;
};

type CiteMetadata = OpenaiWebChatMessageMetadata['_cite_metadata'];

const actions = computed(() => {
  const result = [] as BrowsingAction[];
  let currentCiteMetadata: CiteMetadata | undefined = undefined;
  for (const message of props.messages) {
    const metadata = message.metadata as OpenaiWebChatMessageMetadata;
    if (typeof message.content == 'string') {
      console.error('browsing message.content is string', message);
      continue;
    }
    if (metadata.recipient === 'browser') {
      let code = getContentRawText(message);
      // 过滤掉 code 中 以 # 开头的行
      code = code
        .split('\n')
        .filter((line) => !line.startsWith('#'))
        .join('\n');
      if (code.includes('search(')) {
        // search("...")
        const searchContent = code.match(/search\("(.*)".*\)/)?.[1];
        result.push({
          type: 'search',
          message,
          searchContent,
        });
      } else if (code.includes('click(')) {
        // 例如：click(3)
        const clickIndex = code.match(/click\((.*)\)/)?.[1];
        result.push({
          type: 'click',
          message,
          clickIndex,
          citeMetadata: currentCiteMetadata,
        });
      } else if (code.includes('scroll(')) {
        // 例如：click(3)
        const clickIndex = code.match(/click\((.*)\)/)?.[1];
        result.push({
          type: 'scroll',
          message,
          clickIndex,
          citeMetadata: currentCiteMetadata,
        });
      } else if (code.includes('quote(')) {
        // result.push({
        //   type: 'quote',
        //   message,
        // });
      } else {
        console.warn('unknown browsing action in code', message);
      }
    } else if (message.role === 'tool') {
      if (message.content?.content_type === 'tether_browsing_display') {
        result.push({
          type: 'click_result',
          message,
        });
        if (metadata._cite_metadata) currentCiteMetadata = metadata._cite_metadata;
      } else if (message.content?.content_type === 'tether_quote') {
        result.push({
          type: 'quote_result',
          message,
        });
      } else if (message.content?.content_type === 'system_error') {
        result.push({
          type: 'failed',
          message,
        });
      } else {
        console.warn('unknown browsing action in tool', message);
      }
    } else {
      console.warn('unknown browsing action', message);
    }
  }
  return result;
});

const displayActions = computed(() => {
  // 筛除 actions 中的 quote_result
  return actions.value.filter((action) => action.type !== 'quote_result');
});

function getSearchUrl(searchContent: string | undefined) {
  if (!searchContent) return '#';
  return `https://www.bing.com/search?q=${encodeURIComponent(searchContent)}`;
}

function getCiteUrl(citeIndex: string | number | undefined, citeMetadata: CiteMetadata) {
  if (!citeIndex || !citeMetadata) return '#';
  if (citeMetadata.metadata_list?.length === 1) return citeMetadata.metadata_list[0].url;
  const index = typeof citeIndex === 'number' ? citeIndex : parseInt(citeIndex);
  if (citeMetadata.metadata_list && citeMetadata.metadata_list[index]) {
    return citeMetadata.metadata_list[index].url;
  }
}

function getCiteTitle(citeIndex: string | number | undefined, citeMetadata: CiteMetadata) {
  if (!citeIndex || !citeMetadata) return citeIndex;
  if (citeMetadata.metadata_list?.length === 1) return citeMetadata.metadata_list[0].title;
  const index = typeof citeIndex === 'number' ? citeIndex : parseInt(citeIndex);
  if (citeMetadata.metadata_list && citeMetadata.metadata_list[index]) {
    return citeMetadata.metadata_list[index].title;
  }
}

const expandContent = ref(true);

function handleExpand() {
  expandContent.value = !expandContent.value;
}

function showContent(action: BrowsingAction) {
  Dialog.info({
    title: t('commons.detail'),
    // content: getContentRawText(action.message),
    // 给一个 200px 宽的 div
    content: () =>
      h(
        NScrollbar,
        { style: 'width: "auto"; max-height: 80vh', class: 'whitespace-pre-wrap' },
        { default: () => getContentRawText(action.message) }
      ),
  });
}
</script>

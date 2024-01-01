<template>
  <div class="flex flex-row lt-md:flex-col pt-3 lt-md:pt-2 px-4 relative" :style="{ backgroundColor: backgroundColor }">
    <div class="w-10 lt-md:ml-0 ml-2 mt-3">
      <n-avatar v-if="lastMessage?.role == 'user'" size="small">
        <n-icon>
          <PersonFilled />
        </n-icon>
      </n-avatar>
      <ChatGPTAvatar v-else size="small" :model="lastMessage?.model" />
    </div>
    <div class="ml-4 lt-md:mx-0 w-full min-h-16">
      <!-- Json View -->
      <div v-if="showRawMessage" class="mr-2 my-3 json-viewer">
        <JsonViewer :value="props.messages" copyable expanded :expand-depth="2" :theme="appStore.theme" />
      </div>
      <!-- Rendered -->
      <div v-else class="markdown">
        <div v-for="(item, i) in displayItems" :key="i" class="mr-1">
          <div v-if="item.type == 'text'">
            <MessageRowTextDisplay
              :conversation-id="props.conversationId"
              :render-markdown="renderMarkdown"
              :messages="item.messages"
            />
          </div>
          <div v-else-if="item.type == 'browser'">
            <MessageRowBrowserDisplay :messages="item.messages" />
          </div>
          <div v-else-if="item.type == 'plugin'">
            <MessageRowPluginDisplay :messages="item.messages" />
          </div>
          <div v-else-if="item.type == 'code'">
            <MessageRowCodeDisplay :messages="item.messages" />
          </div>
          <div v-else-if="item.type == 'multimodal_text'">
            <MessageRowMultimodalTextDisplay
              :conversation-id="props.conversationId"
              :render-markdown="renderMarkdown"
              :messages="item.messages"
            />
          </div>
          <div v-else-if="item.type == 'dalle_prompt'">
            <MessageRowDallePromptDisplay :messages="item.messages" />
          </div>
          <div v-else-if="item.type == 'dalle_result'">
            <MessageRowMultimodalTextDalleDisplay
              :conversation-id="props.conversationId"
              :render-markdown="renderMarkdown"
              :messages="item.messages"
            />
          </div>
          <div v-else-if="item.type == 'myfiles_browser'">
            <MessageRowMyFilesBrowserDisplay
              :messages="item.messages"
            />
          </div>
          <div v-if="attachments.length != 0">
            <MessageRowAttachmentDisplay :attachments="attachments" />
          </div>
        </div>
      </div>
      <div class="flex w-full justify-end items-center space-x-4 pb-1">
        <div class="flex flex-row items-center space-x-4">
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-text class="text-[10px]" depth="3">
                {{ relativeTimeString }}
              </n-text>
            </template>
            <span> {{ timeString }}</span>
          </n-tooltip>
          <n-text v-if="props.messages.length > 1" class="text-[10px]" depth="3">
            {{ $t('commons.messagesCount', [props.messages.length]) }}
          </n-text>
        </div>
        <div class="hide-in-print flex flex-row items-center space-x-2">
          <!-- 复制 -->
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button text ghost type="tertiary" size="tiny" @click="copyMessageContent">
                <n-icon>
                  <CopyOutline />
                </n-icon>
              </n-button>
            </template>
            <span>{{ t('commons.copy') }}</span>
          </n-tooltip>
          <!-- 是否渲染 markdown -->
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button text ghost size="tiny" :type="'tertiary'" @click="toggleRenderMarkdown">
                <n-icon :component="renderMarkdown ? ArticleFilled : ArticleOutlined" />
              </n-button>
            </template>
            <span>{{ t('commons.shouldRenderMarkdown') }}</span>
          </n-tooltip>
          <n-tooltip trigger="hover">
            <template #trigger>
              <n-button
                text
                ghost
                size="tiny"
                :type="showRawMessage ? 'success' : 'tertiary'"
                @click="toggleShowRawMessage"
              >
                <n-icon :component="CodeSlash" />
              </n-button>
            </template>
            <span>{{ t('commons.showRawMessage') }}</span>
          </n-tooltip>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import 'vue3-json-viewer/dist/index.css';
import 'highlight.js/styles/atom-one-dark.css';

// import 'highlight.js/lib/common';
import { CodeSlash, CopyOutline } from '@vicons/ionicons5';
import { ArticleFilled, ArticleOutlined, PersonFilled } from '@vicons/material';
import * as clipboard from 'clipboard-polyfill';
import { useThemeVars } from 'naive-ui';
import { computed, onMounted, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { JsonViewer } from 'vue3-json-viewer';

import ChatGPTAvatar from '@/components/ChatGPTAvatar.vue';
import { useAppStore } from '@/store';
import { BaseChatMessage, OpenaiWebChatMessageMetadata } from '@/types/schema';
import { getTextMessageContent, splitMessagesInGroup } from '@/utils/chat';
import { parseTimeString, parseTimeToRelative } from '@/utils/time';
import { Message } from '@/utils/tips';

import { determineMessageType, DisplayItem } from '../utils/message';
import MessageRowAttachmentDisplay from './MessageRowAttachmentDisplay.vue';
import MessageRowBrowserDisplay from './MessageRowBrowserDisplay.vue';
import MessageRowCodeDisplay from './MessageRowCodeDisplay.vue';
import MessageRowDallePromptDisplay from './MessageRowDallePromptDisplay.vue';
import MessageRowMultimodalTextDalleDisplay from './MessageRowMultimodalTextDalleDisplay.vue';
import MessageRowMultimodalTextDisplay from './MessageRowMultimodalTextDisplay.vue';
import MessageRowMyFilesBrowserDisplay from './MessageRowMyFilesBrowserDisplay.vue';
import MessageRowPluginDisplay from './MessageRowPluginDisplay.vue';
import MessageRowTextDisplay from './MessageRowTextDisplay.vue';

const { t } = useI18n();

const themeVars = useThemeVars();

const showRawMessage = ref(false); // 显示原始消息
const appStore = useAppStore();
const renderMarkdown = ref(true);

watch(
  () => appStore.preference.renderUserMessageInMd,
  () => {
    if (lastMessage.value?.role == 'user') renderMarkdown.value = appStore.preference.renderUserMessageInMd;
  }
);

onMounted(() => {
  if (lastMessage.value?.role == 'user') renderMarkdown.value = appStore.preference.renderUserMessageInMd;
});

const props = defineProps<{
  conversationId: string;
  messages: BaseChatMessage[];
}>();

const lastMessage = computed<BaseChatMessage | null>(() => {
  if (props.messages.length == 0) return null;
  else return props.messages[props.messages.length - 1];
});

const timeString = computed<string>(() => {
  if (!lastMessage.value || !lastMessage.value.create_time) return '';
  let create_time = lastMessage.value.create_time;
  return parseTimeString(create_time);
});

const relativeTimeString = computed<string>(() => {
  if (!lastMessage.value || !lastMessage.value.create_time) return '';
  let create_time = lastMessage.value.create_time;
  return parseTimeToRelative(create_time);
});

const messageGroups = computed<BaseChatMessage[][]>(() => {
  return splitMessagesInGroup(props.messages);
});

const displayItems = computed<DisplayItem[]>(() => {
  const result = [] as DisplayItem[];
  for (const group of messageGroups.value) {
    result.push({
      type: determineMessageType(group),
      messages: group,
    });
  }
  return result;
});

const attachments = computed(() => {
  const metadata = lastMessage.value?.metadata as OpenaiWebChatMessageMetadata;
  if (metadata?.attachments) return metadata.attachments;
  else return [];
});

const allTextContent = computed(() => {
  let result = [];
  for (const item of displayItems.value) {
    if (item.type == 'text') {
      result.push(getTextMessageContent(item.messages));
    }
  }
  return result.join('\n\n');
});

const backgroundColor = computed(() => {
  if (lastMessage.value?.role == 'user') {
    return themeVars.value.bodyColor;
  } else {
    return themeVars.value.actionColor;
  }
});

function toggleShowRawMessage() {
  showRawMessage.value = !showRawMessage.value;
}

function toggleRenderMarkdown() {
  renderMarkdown.value = !renderMarkdown.value;
}

function copyMessageContent() {
  clipboard
    .writeText(allTextContent.value)
    .then(() => {
      Message.success(t('commons.copiedToClipboard'));
    })
    .catch(() => {
      console.error('Failed to copy message content to clipboard.');
    });
}
</script>

<style>
/* modified from https://github.com/arronhunt/highlightjs-copy */

.json-viewer * {
  font-size: 0.6rem;
}

.markdown pre {
  @apply w-full flex;
}

.markdown pre code {
  /* @apply w-full max-w-94 sm: max-w-138 md:max-w-156 lg:max-w-170 */
  @apply w-0 flex-grow mr-0;
  font-size: 0.8rem;
  font-family: Menlo, ui-monospace, SFMono-Regular, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

@media print {
  code,
  .code-result {
    @apply max-w-160 !important
    @apply whitespace-pre-line;
  }
  .hide-in-print {
    @apply hidden;
  }
}

.markdown p {
  white-space: pre-line;
}

.markdown p:last-child {
  margin-bottom: 0;
}

.katex-error {
  @apply text-red-500;
}

.markdown ol,
ul {
  padding-left: 16px;
}

a.sandbox {
  /* text-decoration-line: none !important; */
}

.markdown a {
  text-decoration-line: underline;
  text-underline-offset: 2px;
  font-weight: 500;
  /* color: var(--n-text-color); */
  @apply text-blue-500;
}

.markdown table {
  border: gray 1px solid;
  @apply min-w-1/2 text-center border-collapse;
}

.markdown tr {
  border: gray 1px solid;
}

.markdown th {
  border: gray 1px solid;
  @apply bg-gray-400;
}

.markdown td {
  border: gray 1px solid;
}

.hljs-copy-wrapper {
  position: relative;
  overflow: hidden;
}

.hljs-copy-wrapper:hover .hljs-copy-button,
.hljs-copy-button:focus {
  transform: translateX(0);
}

.hljs-copy-button {
  position: absolute;
  transform: translateX(calc(100% + 2em));
  top: 1em;
  right: 1.2em;
  width: 2rem;
  height: 2rem;
  text-indent: -9999px;
  /* Hide the inner text */
  color: #c5c5c5;
  border-radius: 0.25rem;
  border: 1px solid #c5c5c522;
  /* background-color: #2d2b57; */

  /* 白色，不透明度10% */
  background-color: #ffffff1a;
  background-image: url('data:image/svg+xml;utf-8,<svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path fill-rule="evenodd" clip-rule="evenodd" d="M6 5C5.73478 5 5.48043 5.10536 5.29289 5.29289C5.10536 5.48043 5 5.73478 5 6V20C5 20.2652 5.10536 20.5196 5.29289 20.7071C5.48043 20.8946 5.73478 21 6 21H18C18.2652 21 18.5196 20.8946 18.7071 20.7071C18.8946 20.5196 19 20.2652 19 20V6C19 5.73478 18.8946 5.48043 18.7071 5.29289C18.5196 5.10536 18.2652 5 18 5H16C15.4477 5 15 4.55228 15 4C15 3.44772 15.4477 3 16 3H18C18.7956 3 19.5587 3.31607 20.1213 3.87868C20.6839 4.44129 21 5.20435 21 6V20C21 20.7957 20.6839 21.5587 20.1213 22.1213C19.5587 22.6839 18.7957 23 18 23H6C5.20435 23 4.44129 22.6839 3.87868 22.1213C3.31607 21.5587 3 20.7957 3 20V6C3 5.20435 3.31607 4.44129 3.87868 3.87868C4.44129 3.31607 5.20435 3 6 3H8C8.55228 3 9 3.44772 9 4C9 4.55228 8.55228 5 8 5H6Z" fill="black"/><path fill-rule="evenodd" clip-rule="evenodd" d="M7 3C7 1.89543 7.89543 1 9 1H15C16.1046 1 17 1.89543 17 3V5C17 6.10457 16.1046 7 15 7H9C7.89543 7 7 6.10457 7 5V3ZM15 3H9V5H15V3Z" fill="black"/></svg>');
  background-repeat: no-repeat;
  background-position: center;
  transition: background-color 200ms ease, transform 200ms ease-out;
}

.hljs-copy-button:hover {
  border-color: #91919144;
}

.hljs-copy-button:active {
  border-color: #49494966;
}

.hljs-copy-button[data-copied='true'] {
  text-indent: 0px;
  /* Shows the inner text */
  width: auto;
  background-image: none;
}

@media (prefers-reduced-motion) {
  .hljs-copy-button {
    transition: none;
  }
}

/* visually-hidden */
.hljs-copy-alert {
  clip: rect(0 0 0 0);
  clip-path: inset(50%);
  height: 1px;
  overflow: hidden;
  position: absolute;
  white-space: nowrap;
  width: 1px;
  color: #2d2b57;
}
</style>

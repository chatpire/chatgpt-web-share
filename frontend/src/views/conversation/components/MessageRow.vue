<template>
  <div class="flex flex-row lt-md:flex-col py-3 lt-md:py-2 px-4 relative" :style="{ backgroundColor: backgroundColor }">
    <div class="w-10 lt-md:ml-0 ml-2 mt-3">
      <n-avatar v-if="lastMessage?.role == 'user'" size="small">
        <n-icon>
          <PersonFilled />
        </n-icon>
      </n-avatar>
      <ChatGPTAvatar v-else size="small" :model="lastMessage?.model" />
    </div>
    <div class="lt-md:mx-0 mx-4 w-full">
      <div v-if="showRawMessage" class="my-3 w-full text-gray-500 whitespace-pre-wrap">
        {{ content }}
      </div>
      <!-- <div v-else-if="isPluginMessage" class="my-3">
        <n-alert
          :title="t('commons.invoking_plugin', [openaiWebMetadata?.recipient])"
          type="info"
          class="whitespace-pre-wrap"
        >
          {{ content }}
        </n-alert>
      </div>
      <div v-else-if="isPluginResult" class="my-3">
        <n-alert :title="openaiWebMetadata?.invoked_plugin?.namespace" type="success" class="whitespace-pre-wrap">
          {{ content }}
        </n-alert>
      </div> -->
      <!-- 文本内容-->
      <div v-else>
        <div
          v-if="renderPureText"
          ref="contentRef"
          class="message-content w-full whitespace-pre-wrap py-4"
        >
          {{ renderedContent }}
        </div>
        <div
          v-else
          ref="contentRef"
          class="message-content w-full"
          v-html="renderedContent"
        />
      <!-- 用户回复不渲染为markdown -->
      </div>

      <div class="hide-in-print">
        <n-button
          text
          ghost
          type="tertiary"
          size="tiny"
          class="mt-2 -ml-2 absolute lt-sm:bottom-3 lt-sm:right-3 bottom-2 right-2"
          @click="copyMessageContent"
        >
          <n-icon>
            <CopyOutline />
          </n-icon>
        </n-button>
        <n-button
          text
          ghost
          size="tiny"
          :type="showRawMessage ? 'success' : 'tertiary'"
          class="mt-2 -ml-2 absolute lt-sm:bottom-3 lt-sm:right-9 bottom-2 right-6"
          @click="toggleShowRawMessage"
        >
          <n-icon>
            <CodeSlash />
          </n-icon>
        </n-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { CodeSlash, CopyOutline } from '@vicons/ionicons5';
import { PersonFilled } from '@vicons/material';
import * as clipboard from 'clipboard-polyfill';
import { useThemeVars } from 'naive-ui';
import { computed, onMounted, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import ChatGPTAvatar from '@/components/ChatGPTAvatar.vue';
import { useAppStore } from '@/store';
import { BaseChatMessage } from '@/types/schema';
import { getContentRawText } from '@/utils/chat';
import md from '@/utils/markdown';
import { Message } from '@/utils/tips';

const { t } = useI18n();
const appStore = useAppStore();

const themeVars = useThemeVars();

const contentRef = ref<HTMLDivElement>();
const showRawMessage = ref(false); // 显示原始消息

const props = defineProps<{
  messages: BaseChatMessage[];
}>();

const lastMessage = computed<BaseChatMessage | null>(() => {
  if (props.messages.length == 0) return null;
  else return props.messages[props.messages.length - 1];
});

const renderPureText = computed(() => {
  // 对于 user 的内容，默认按纯文本来渲染
  return appStore.preference.renderUserMessageInMd === false && lastMessage.value?.role == 'user';
});

const toggleShowRawMessage = () => {
  showRawMessage.value = !showRawMessage.value;
};

const backgroundColor = computed(() => {
  if (lastMessage.value?.role == 'user') {
    return themeVars.value.bodyColor;
  } else {
    return themeVars.value.actionColor;
  }
});

const content = computed(() => {
  // return getContentRawText(lastMessage.value);
  let result = '';
  // 遍历 props.messages
  // 如果 message.content.content_type == 'text' 则加入 result，其它跳过
  for (let i = 0; i < props.messages.length; i++) {
    const message = props.messages[i] as BaseChatMessage;
    if (!message || !message.content) continue;
    if (typeof message.content == 'string') result += message.content;
    else if (message.content.content_type == 'text') {
      result += getContentRawText(message);
    }
  }
  return result;
});

const renderedContent = computed(() => {
  if (renderPureText.value) {
    return content.value;
  }
  const result = md.render(content.value || '');
  return addButtonsToPreTags(result);
});

// ---- 用于为代码块添加 copy 按钮 ----

function addButtonsToPreTags(htmlString: string): string {
  // Parse the HTML string into an Element object.
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlString, 'text/html');

  // Get all the <pre> elements in the document.
  const preTags = doc.getElementsByTagName('pre');

  // Loop through the <pre> elements and add a <button> to each one.
  for (let i = 0; i < preTags.length; i++) {
    const preTag = preTags[i];

    const button = Object.assign(document.createElement('button'), {
      innerHTML: '',
      className: 'hljs-copy-button hide-in-print',
    });
    button.dataset.copied = 'false';
    preTag.classList.add('hljs-copy-wrapper');

    // Add a custom proprety to the code block so that the copy button can reference and match its background-color value.
    preTag.style.setProperty('--hljs-theme-background', window.getComputedStyle(preTag).backgroundColor);

    if (appStore.preference.codeAutoWrap) {
      preTag.style.cssText += 'white-space: pre-wrap; word-wrap: break-word; word-break: break-all;';
    }

    preTag.appendChild(button);
  }

  // Serialize the modified Element object back into a string.
  const serializer = new XMLSerializer();
  return serializer.serializeToString(doc.documentElement);
}

let observer = null;
onMounted(() => {
  if (!contentRef.value) return;
  // eslint-disable-next-line no-undef
  const callback: MutationCallback = (mutations: MutationRecord[]) => {
    for (const mutation of mutations) {
      if (mutation.type === 'childList') {
        bindOnclick();
      }
    }
  };
  observer = new MutationObserver(callback);
  observer.observe(contentRef.value, { subtree: true, childList: true });
  bindOnclick();
});

const bindOnclick = () => {
  // 获取模板引用中的所有 pre 元素和其子元素中的 button 元素
  const preElements = contentRef.value?.querySelectorAll('pre');
  if (!preElements) return;
  for (const preElement of preElements as any) {
    for (const button of preElement.querySelectorAll('button')) {
      (button as HTMLButtonElement).onmousedown = () => {
        // 如果按钮的内容为 "Copied!"，则跳过复制操作
        if (button.innerHTML === 'Copied!') {
          return;
        }

        const preContent = button.parentElement!.cloneNode(true) as HTMLElement;
        preContent.removeChild(preContent.querySelector('button')!);

        // Remove the alert element if it exists in preContent
        const alertElement = preContent.querySelector('.hljs-copy-alert');
        if (alertElement) {
          preContent.removeChild(alertElement);
        }

        clipboard
          .writeText(preContent.textContent || '')
          .then(function () {
            button.innerHTML = 'Copied!';
            button.dataset.copied = 'true';

            let alert: HTMLDivElement | null = Object.assign(document.createElement('div'), {
              role: 'status',
              className: 'hljs-copy-alert',
              innerHTML: 'Copied to clipboard',
            });
            button.parentElement!.appendChild(alert);

            setTimeout(() => {
              if (alert) {
                button.innerHTML = 'Copy';
                button.dataset.copied = 'false';
                button.parentElement!.removeChild(alert);
                alert = null;
              }
            }, 2000);
          })
          .then();
      };
    }
  }
};

// ------

const copyMessageContent = () => {
  const messageContent = content.value || '';
  clipboard
    .writeText(messageContent)
    .then(() => {
      Message.success(t('commons.copiedToClipboard'));
    })
    .catch(() => {
      console.error('Failed to copy message content to clipboard.');
    });
};
</script>

<style>
/* modified from https://github.com/arronhunt/highlightjs-copy */

pre {
  @apply w-full flex;
}

pre code {
  /* @apply w-full max-w-94 sm: max-w-138 md:max-w-156 lg:max-w-170 */
  @apply w-0 flex-grow mr-0;
  font-size: 0.8rem;
  font-family: Menlo, ui-monospace, SFMono-Regular, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;
}

@media print {
  code {
    @apply max-w-160 !important
    @apply whitespace-pre-line;
  }
}

p {
  white-space: pre-line;
}

ol,
ul {
  padding-left: 16px;
}

.message-content table {
  border: gray 1px solid;
  @apply min-w-1/2 text-center border-collapse;
}

.message-content tr {
  border: gray 1px solid;
}

.message-content th {
  border: gray 1px solid;
  @apply bg-gray-400;
}

.message-content td {
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

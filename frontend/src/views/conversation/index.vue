<template>
  <n-layout
    ref="rootRef"
    has-sider
    :class="['h-full', !appStore.preference.widerConversationPage ? 'lg:w-screen-lg lg:mx-auto' : '']"
  >
    <!-- 左栏 -->
    <n-layout-sider
      :native-scrollbar="false"
      :collapsed-width="0"
      collapse-mode="transform"
      trigger-style="top: 27px; right: -26px;"
      collapsed-trigger-style="top: 27px; right: -26px;"
      bordered
      show-trigger="arrow-circle"
      :width="260"
      class="h-full"
    >
      <LeftBar
        v-show="!foldLeftBar"
        v-model:value="currentConversationId"
        :class="['h-full pt-4 px-4 box-border mb-4 overflow-hidden flex flex-col space-y-4']"
        :loading="loadingBar"
        @new-conversation="makeNewConversation"
      />
    </n-layout-sider>
    <!-- 右栏 -->
    <n-layout-content embeded :class="['flex flex-col overflow-hidden', gtmd() ? '' : 'min-w-100vw']">
      <div class="h-full relative flex flex-col">
        <!-- 消息记录内容（用于全屏展示） -->
        <n-scrollbar
          v-if="currentConversationId"
          ref="historyRef"
          class="relative"
          :content-style="loadingHistory ? { height: '100%' } : {}"
        >
          <!-- 回到底部按钮 -->
          <div class="right-2 bottom-5 absolute z-20">
            <n-button secondary circle size="small" @click="scrollToBottomSmooth">
              <template #icon>
                <n-icon :component="ArrowDown" />
              </template>
            </n-button>
          </div>
          <HistoryContent
            ref="historyContentRef"
            :conversation-id="currentConversationId"
            :extra-messages="currentActiveMessages"
            :fullscreen="false"
            :show-tips="showFullscreenTips"
            :loading="loadingHistory"
          />
        </n-scrollbar>
        <!-- 未选中对话（空界面） -->
        <div
          v-else-if="!currentConversationId"
          class="flex-grow flex flex-col justify-center"
          :style="{ backgroundColor: themeVars.cardColor }"
        >
          <n-empty v-if="!currentConversation" :description="$t('tips.loadConversation')">
            <template #icon>
              <n-icon>
                <ChatboxEllipses />
              </n-icon>
            </template>
            <template #extra>
              <n-button @click="makeNewConversation">
                {{ $t('tips.newConversation') }}
              </n-button>
            </template>
          </n-empty>
        </div>
        <!-- 下半部分（回复区域） -->
        <InputRegion
          v-model:input-value="inputValue"
          v-model:auto-scrolling="autoScrolling"
          class="sticky bottom-0 z-10"
          :can-abort="canAbort"
          :send-disabled="sendDisabled"
          @abort-request="abortRequest"
          @export-to-markdown-file="exportToMarkdownFile"
          @export-to-pdf-file="exportToPdfFile"
          @send-msg="sendMsg"
          @show-fullscreen-history="showFullscreenHistory"
        />
      </div>
    </n-layout-content>
  </n-layout>
</template>

<script setup lang="ts">
import { ArrowDown, ChatboxEllipses } from '@vicons/ionicons5';
import { RemovableRef, useStorage } from '@vueuse/core';
import { NButton, NIcon, useThemeVars } from 'naive-ui';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { getAskWebsocketApiUrl } from '@/api/chat';
import { useAppStore, useConversationStore, useUserStore } from '@/store';
import { newConversationId } from '@/store/modules/conversation';
import { NewConversationInfo } from '@/types/custom';
import {
  AskRequest,
  AskResponse,
  BaseChatMessage,
  BaseConversationHistory,
  BaseConversationSchema,
} from '@/types/schema';
import { screenWidthGreaterThan } from '@/utils/media';
import { popupNewConversationDialog } from '@/utils/renders';
// import { popupNewConversationDialog } from '@/utils/renders';
import { Dialog, LoadingBar, Message } from '@/utils/tips';
import HistoryContent from '@/views/conversation/components/HistoryContent.vue';
import InputRegion from '@/views/conversation/components/InputRegion.vue';
import LeftBar from '@/views/conversation/components/LeftBar.vue';

import { saveAsMarkdown } from './utils/export';

const themeVars = useThemeVars();

const { t } = useI18n();

const gtmd = screenWidthGreaterThan('md');

const rootRef = ref();
const historyRef = ref();
const userStore = useUserStore();
const appStore = useAppStore();
const conversationStore = useConversationStore();

const loadingBar = ref(false);
const loadingHistory = ref<boolean>(false);
const autoScrolling = ref<boolean>(true);

const isAborted = ref<boolean>(false);
const canAbort = ref<boolean>(false);
const foldLeftBar = ref<RemovableRef<boolean>>(useStorage('foldLeftBar', false));
let aborter: (() => void) | null = null;

const hasNewConversation = ref<boolean>(false);
const currentConversationId = ref<string | null>(null);
const currentConversation = computed<BaseConversationSchema | null>(() => {
  if (currentConversationId.value === conversationStore.newConversation?.conversation_id)
    return conversationStore.newConversation;
  const conv = conversationStore.conversations?.find((conversation: BaseConversationSchema) => {
    return conversation.conversation_id == currentConversationId.value;
  });
  return conv || null;
});
const currentConvHistory = computed<BaseConversationHistory | null>(() => {
  if (!currentConversationId.value) return null;
  return conversationStore.conversationHistoryMap[currentConversationId.value] || null;
});

const inputValue = ref('');
const currentSendMessage = ref<BaseChatMessage | null>(null);
const currentRecvMessages = ref<BaseChatMessage[]>([]);

// 实际的 currentMessageList，加上当前正在发送的消息
const currentActiveMessages = computed<Array<BaseChatMessage>>(() => {
  const result: BaseChatMessage[] = [];
  if (currentSendMessage.value) result.push(currentSendMessage.value);
  for (const msg of currentRecvMessages.value) {
    result.push(msg);
  }
  // console.log('currentActiveMessages', currentActiveMessages.value, currentRecvMessages.value);
  return result;
});

watch(currentConversationId, (newVal, _oldVal) => {
  if (newVal != 'new_conversation') {
    handleChangeConversation(newVal);
  }
});

const handleChangeConversation = (key: string | null) => {
  // TODO: 清除当前已询问、得到回复，但是发生错误的两条消息
  if (loadingBar.value || !key) return;
  loadingBar.value = true;
  loadingHistory.value = true;
  LoadingBar.start();
  conversationStore
    .fetchConversationHistory(key)
    .then(() => {
      // console.log(conversationStore.conversationDetailMap);
    })
    .catch((err: any) => {
      console.log(err);
    })
    .finally(() => {
      loadingBar.value = false;
      loadingHistory.value = false;
      LoadingBar.finish();
    });
};

const sendDisabled = computed(() => {
  return (
    loadingBar.value ||
    currentConversationId.value == null ||
    inputValue.value === null ||
    inputValue.value.trim() == ''
  );
});

const makeNewConversation = () => {
  if (hasNewConversation.value) return;
  popupNewConversationDialog(async (newConversationInfo: NewConversationInfo) => {
    console.log('makeNewConversation', newConversationInfo);
    if (!newConversationInfo.source || !newConversationInfo.model) return;
    newConversationInfo.title = newConversationInfo.title || `New Chat (${t('sources_short.' + newConversationInfo.source)})`;
    conversationStore.createNewConversation(newConversationInfo);
    currentConversationId.value = conversationStore.newConversation!.conversation_id!;
  });
};

const abortRequest = () => {
  if (aborter == null || !canAbort.value) return;
  aborter();
  aborter = null;
};

const scrollToBottom = () => {
  historyRef.value.scrollTo({ left: 0, top: historyRef.value.$refs.scrollbarInstRef.contentRef.scrollHeight });
};

const scrollToBottomSmooth = () => {
  historyRef.value.scrollTo({
    left: 0,
    top: historyRef.value.$refs.scrollbarInstRef.contentRef.scrollHeight,
    behavior: 'smooth',
  });
};

function buildTemporaryMessage(role: string, content: string, parent: string | undefined, model: string | undefined) {
  const random_strid = Math.random().toString(36).substring(2, 16);
  return {
    id: `temp_${random_strid}`,
    source: currentConversation.value!.source,
    content,
    role: role,
    parent, // 其实没有用到parent
    children: [],
    model
  };
}

const sendMsg = async () => {
  if (sendDisabled.value || loadingBar.value || currentConvHistory.value == null) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }

  LoadingBar.start();
  loadingBar.value = true;
  const text = inputValue.value;
  inputValue.value = '';

  canAbort.value = false;
  isAborted.value = false;
  let hasGotReply = false;

  const askRequest: AskRequest = {
    source: currentConversation.value!.source,
    new_conversation: currentConversationId.value!.startsWith('new_conversation'),
    model: currentConversation.value!.current_model!,
    content: text,
    openai_web_plugin_ids: currentConvHistory.value!.metadata?.source === 'openai_web' ? currentConvHistory.value!.metadata?.plugin_ids : undefined,
  };
  if (conversationStore.newConversation) {
    askRequest.new_title = conversationStore.newConversation.title;
  } else {
    askRequest.conversation_id = currentConversationId.value!;
    askRequest.parent = currentConvHistory.value.current_node;
  }

  // 使用临时的随机 id 保持当前更新的两个消息
  currentSendMessage.value = buildTemporaryMessage('user', text, currentConvHistory.value?.current_node, currentConversation.value!.current_model!);
  currentRecvMessages.value = [buildTemporaryMessage('assistant', '...', currentSendMessage.value.id, currentConversation.value!.current_model!)];
  const wsUrl = getAskWebsocketApiUrl();
  let hasError = false;
  let wsErrorMessage: AskResponse | null = null;
  console.log('Connecting to', wsUrl, askRequest);
  const webSocket = new WebSocket(wsUrl);

  let respConversationId = null as string | null;

  webSocket.onopen = (_event: Event) => {
    webSocket.send(JSON.stringify(askRequest));
  };

  webSocket.onmessage = (event: MessageEvent) => {
    const response = JSON.parse(event.data) as AskResponse;
    // console.log('Received message from server:', reply);
    if (response.type === 'waiting') {
      // 等待回复
      canAbort.value = false;
      currentRecvMessages.value![0].content = t(response.tip || 'tips.waiting');
    } else if (response.type === 'queueing') {
      // 正在排队
      canAbort.value = true;
      currentRecvMessages.value![0].content = t(response.tip || 'tips.queueing');
    } else if (response.type === 'message') {
      if (!hasGotReply) {
        currentRecvMessages.value = [];
        hasGotReply = true;
      }
      const message = response.message as BaseChatMessage;
      if (message.role !== 'user') {
        const index = currentRecvMessages.value.findIndex((msg) => msg.id === message.id);
        if (index === -1) {
          currentRecvMessages.value.push(message);
        } else {
          currentRecvMessages.value[index] = message;
        }
      }
      // console.log('got message', message, index, currentRecvMessages.value);
      respConversationId = response.conversation_id || null;
      canAbort.value = true;
    } else if (response.type === 'error') {
      hasError = true;
      console.error('websocket received error message', response);
      wsErrorMessage = response;
    }
    if (autoScrolling.value) scrollToBottom();
  };

  webSocket.onclose = async (event: CloseEvent) => {
    aborter = null;
    canAbort.value = false;
    console.log('WebSocket connection is closed', event, isAborted.value);
    if (!hasError && (event.code == 1000 || isAborted.value)) {
      // 正常关闭
      if (hasGotReply) {
        const allNewMessages = [currentSendMessage.value] as BaseChatMessage[];
        for (const msg of currentRecvMessages.value) {
          allNewMessages.push(msg);
        }

        if (currentConversationId.value == newConversationId) {
          const newConvHistory = {
            _id: respConversationId!,
            source: 'openai_web',
            title: currentConvHistory.value!.title,
            current_model: currentConvHistory.value!.current_model,
            create_time: currentConvHistory.value!.create_time,
            update_time: currentConvHistory.value!.update_time,
            metadata: currentConvHistory.value!.metadata,
            mapping: {},
            current_node: '',
          } as BaseConversationHistory;
          conversationStore.$patch({
            conversationHistoryMap: {
              [respConversationId!]: newConvHistory,
            },
          });
        }
        conversationStore.addMessagesToConversation(respConversationId!, allNewMessages);
        currentSendMessage.value = null;
        currentRecvMessages.value = [];
        currentConversationId.value = respConversationId!; // 这里将会导致 currentConversation 切换
        await conversationStore.fetchAllConversations();
        conversationStore.removeNewConversation();
        console.log('done', allNewMessages, currentConversationId.value);
      }
    } else {
      let content = '';
      if (wsErrorMessage != null) {
        if (wsErrorMessage.tip) {
          content = t(wsErrorMessage.tip);
        } else {
          content = wsErrorMessage.error_detail || t('errors.unknown');
        }
      } else {
        content = `WebSocket ${event.code}: ${t(event.reason || 'errors.unknown')}`;
      }
      Dialog.error({
        title: t('errors.askError'),
        content,
        positiveText: t('commons.withdrawMessage'),
        negativeText: t('commons.cancel'),
        onPositiveClick: () => {
          currentSendMessage.value = null;
          currentRecvMessages.value = [];
        },
      });
    }
    await userStore.fetchUserInfo();
    LoadingBar.finish();
    loadingBar.value = false;
    isAborted.value = false;
  };

  webSocket.onerror = (event: Event) => {
    console.error('WebSocket error:', event);
  };

  aborter = () => {
    isAborted.value = true;
    webSocket.close();
  };
};

const exportToMarkdownFile = () => {
  if (!currentConversation.value) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }
  saveAsMarkdown(currentConvHistory.value!);
};

const historyContentRef = ref();
const showFullscreenTips = ref(false);

const showFullscreenHistory = () => {
  if (!currentConversation.value) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }
  // focus historyContentRef
  historyContentRef.value.focus();
  historyContentRef.value.toggleFullscreenHistory(true);
};

const exportToPdfFile = () => {
  if (!currentConversation.value) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }
  historyContentRef.value.toggleFullscreenHistory(false);
  window.print();
  historyContentRef.value.toggleFullscreenHistory(false);
};

// 加载对话列表
conversationStore.fetchAllConversations().then();
</script>

<style>
textarea.n-input__textarea-el {
  resize: none;
}

div.n-menu-item-content-header {
  display: flex;
  justify-content: space-between;
}

span.n-menu-item-content-header__extra {
  display: inline-block;
}

.left-col .n-card__content {
  @apply flex flex-col overflow-auto !important;
}

@media print {
  body * {
    visibility: hidden;
  }

  #print-content * {
    visibility: visible;
  }

  /* no margin in page */
  @page {
    margin-left: 0;
    margin-right: 0;
  }
}
</style>

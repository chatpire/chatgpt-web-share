<template>
  <div
    ref="rootRef"
    :class="[
      'flex-grow flex flex-col md:flex-row',
      !appStore.preference.widerConversationPage ? 'lg:w-screen-lg lg:mx-auto' : '',
    ]"
  >
    <!-- 左栏 -->
    <LeftBar
      v-show="!foldLeftBar"
      v-model:value="currentConversationId"
      :class="[
        'md:min-w-50 pl-4 lt-md:pr-4 box-border mb-4 lt-md:h-56 md:flex-grow overflow-hidden flex flex-col space-y-4',
        appStore.preference.widerConversationPage ? 'md:w-1/5' : 'md:w-1/4',
      ]"
      :loading="loadingBar"
      :new-conv="newConversation"
      @new-conversation="makeNewConversation"
    />
    <!-- 右栏 -->
    <div
      :class="['flex-grow flex flex-col md:px-4', appStore.preference.widerConversationPage ? 'md:w-4/5' : 'md:w-3/4']"
    >
      <n-card
        class="flex-grow md:mb-4 relative"
        :bordered="true"
        content-style="padding: 0; display: flex; flex-direction: column; "
      >
        <!-- 展开/收起左栏 -->
        <div class="left-3 top-3 absolute z-20">
          <n-button
            strong
            secondary
            :type="foldLeftBar ? 'default' : 'primary'"
            size="small"
            @click="foldLeftBar = !foldLeftBar"
          >
            <template #icon>
              <n-icon :component="MenuRound" />
            </template>
          </n-button>
        </div>
        <!-- 回到底部按钮 -->
        <div class="right-2 bottom-30 absolute z-20">
          <n-button secondary circle size="small" @click="scrollToBottomSmooth">
            <template #icon>
              <n-icon :component="ArrowDown" />
            </template>
          </n-button>
        </div>
        <!-- 消息记录内容（用于全屏展示） -->
        <n-scrollbar
          v-if="currentConversationId"
          ref="historyRef"
          class="h-0 flex-grow"
          :content-style="loadingHistory ? { height: '100%' } : {}"
        >
          <HistoryContent
            ref="historyContentRef"
            :messages="currentMessageListToDisplay"
            :fullscreen="false"
            :model-name="currentConversation?.current_model || ''"
            :show-tips="showFullscreenTips"
            :loading="loadingHistory"
          >
            <template #top>
              <div
                class="flex justify-center py-4 px-4 max-w-full relative"
                :style="{ backgroundColor: themeVars.baseColor }"
              >
                <n-text>
                  {{ $t('commons.currentConversationModel') }}: 
                  {{ getChatModelNameTrans(currentConversation?.current_model || null) }} {{ t(`labels.${currentConversation?.type}`) }}
                </n-text>
              </div>
            </template>
          </HistoryContent>
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
          :can-abort="canAbort"
          :send-disabled="sendDisabled"
          @abort-request="abortRequest"
          @export-to-markdown-file="exportToMarkdownFile"
          @export-to-pdf-file="exportToPdfFile"
          @send-msg="sendMsg"
          @show-fullscreen-history="showFullscreenHistory"
        />
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ArrowDown, ChatboxEllipses } from '@vicons/ionicons5';
import { MenuRound } from '@vicons/material';
import { RemovableRef, useStorage } from '@vueuse/core';
import { NButton, NIcon, useThemeVars } from 'naive-ui';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { AskInfo, getAskWebsocketApiUrl } from '@/api/chat';
import { useAppStore, useConversationStore, useUserStore } from '@/store';
import {NewConversationInfo} from '@/types/custom';
import { AskRequest, AskResponse, BaseConversationSchema, ChatMessage, ConversationHistoryDocument,RevConversationSchema  } from '@/types/schema';
import { getChatModelNameTrans } from '@/utils/chat';
import { getMessageListFromHistory } from '@/utils/conversation';
import { popupNewConversationDialog } from '@/utils/renders';
// import { popupNewConversationDialog } from '@/utils/renders';
import { Dialog, LoadingBar, Message } from '@/utils/tips';
import HistoryContent from '@/views/conversation/components/HistoryContent.vue';
import InputRegion from '@/views/conversation/components/InputRegion.vue';
import LeftBar from '@/views/conversation/components/LeftBar.vue';

import { saveAsMarkdown } from './utils/export';

const themeVars = useThemeVars();

const { t } = useI18n();

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

const newConversation = ref<BaseConversationSchema | null>(null);
const currentConversationId = ref<string | null>(null);
const currentConversation = computed<BaseConversationSchema | null>(() => {
  if (newConversation.value?.conversation_id === currentConversationId.value)
    return newConversation.value;
  const conv = conversationStore.conversations?.find((conversation: BaseConversationSchema) => {
    return conversation.conversation_id == currentConversationId.value;
  });
  return conv || null;
});

const inputValue = ref('');
const currentSendMessage = ref<ChatMessage | null>(null);
const currentRecvMessage = ref<ChatMessage | null>(null);
const currentMessageListToDisplay = computed<ChatMessage[]>(() => {
  const conversationId = currentConversationId.value;
  if (!conversationId) return [];
  const convHistory = conversationStore.conversationHistoryMap[conversationId];
  let result = getMessageListFromHistory(convHistory);
  if (currentActiveMessages.value.length > 0) {
    result = result.concat(currentActiveMessages.value);
  }
  return result;
});

// 从 store 中获取当前对话最新消息的 id
const currentNode = computed<string | null>(() => {
  if (currentConversation.value?.conversation_id)
    return conversationStore.conversationHistoryMap[currentConversation.value?.conversation_id]?.current_node;
  else return null;
});

// 实际的 currentMessageList，加上当前正在发送的消息
const currentActiveMessages = computed<Array<ChatMessage>>(() => {
  const result: ChatMessage[] = [];
  if (
    currentSendMessage.value &&
    result.findIndex((message) => message.id === currentSendMessage.value?.id) === -1
  )
    result.push(currentSendMessage.value);
  if (
    currentRecvMessage.value &&
    result.findIndex((message) => message.id === currentRecvMessage.value?.id) === -1
  )
    result.push(currentRecvMessage.value);
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
  if (newConversation.value) return;
  popupNewConversationDialog(async (newConversationInfo: NewConversationInfo) => {
    newConversation.value = {
      conversation_id: 'new_conversation',
      type: newConversationInfo.type,
      title: newConversationInfo.title,
      current_model: newConversationInfo.model,
      create_time: new Date().toISOString(), // 仅用于当前排序到顶部
    } as BaseConversationSchema;
    currentConversationId.value = 'new_conversation';
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

const sendMsg = async () => {
  if (sendDisabled.value || loadingBar.value) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }

  LoadingBar.start();
  loadingBar.value = true;
  const message = inputValue.value;
  inputValue.value = '';

  canAbort.value = false;
  isAborted.value = false;
  let hasGotReply = false;

  const askRequest: AskRequest = {
    type: currentConversation.value!.type,
    new_conversation: newConversation.value != null,
    model: currentConversation.value!.current_model!,
    content: message,
  };
  if (newConversation.value) {
    askRequest.new_title = newConversation.value.title;
  } else {
    askRequest.conversation_id = currentConversation.value!.conversation_id;
    askRequest.parent = currentNode.value!;
  }

  // 使用临时的随机 id 保持当前更新的两个消息
  const random_strid = Math.random().toString(36).substring(2, 16);
  currentSendMessage.value = {
    id: `send_${random_strid}`,
    content: message,
    role: 'user',
    parent: currentNode.value || undefined,
    children: [`recv_${random_strid}`],
  };
  currentRecvMessage.value = {
    id: `recv_${random_strid}`,
    content: '',
    role: 'assistent',
    parent: `send_${random_strid}`,
    children: [],
    model: currentConversation.value?.current_model,
  };
  const wsUrl = getAskWebsocketApiUrl();
  let wsErrorMessage: string | null = null;
  console.log('Connecting to', wsUrl, askRequest);
  const webSocket = new WebSocket(wsUrl);

  webSocket.onopen = (_event: Event) => {
    // console.log('WebSocket connection is open', askInfo);
    webSocket.send(JSON.stringify(askRequest));
  };

  webSocket.onmessage = (event: MessageEvent) => {
    const response = JSON.parse(event.data) as AskResponse;
    // console.log('Received message from server:', reply);
    if (response.type === 'waiting') {
      // 等待回复
      canAbort.value = false;
      currentRecvMessage.value!.content = t(response.tip || 'tips.waiting');
    } else if (response.type === 'queueing') {
      // 正在排队
      canAbort.value = true;
      currentRecvMessage.value!.content = t(response.tip || 'tips.queueing');
    } else if (response.type === 'message') {
      // console.log(reply)
      hasGotReply = true;
      currentRecvMessage.value = response.message!;
      canAbort.value = true;
    } else if (response.type === 'error') {
      currentRecvMessage.value!.content = `${t(response.tip || 'error')}: ${response.error_detail}}`;
      console.error(response);
      if (response.error_detail) {
        wsErrorMessage = response.error_detail;
      }
    }
    if (autoScrolling.value) scrollToBottom();
  };

  webSocket.onclose = async (event: CloseEvent) => {
    aborter = null;
    canAbort.value = false;
    console.log('WebSocket connection is closed', event, isAborted.value);
    if (isAborted.value || event.code === 1000) {
      // 正常关闭
      if (hasGotReply) {
        if (newConversation.value) {
          // 解析 ISO string 为 小数时间戳
          const create_time = new Date(newConversation.value.create_time!).getTime() / 1000;
          const newConvHistory = {
            _id: currentConversationId.value,
            type: 'rev',
            title: newConversation.value!.title,
            current_model: newConversation.value!.current_model,
            create_time: `${create_time}`,
            update_time: `${create_time}`,
            mapping: {},
            current_node: '',
          } as ConversationHistoryDocument;
          conversationStore.$patch({
            conversationHistoryMap: {
              [newConversation.value.conversation_id!]: newConvHistory,
            },
          });
          const msgSend = currentSendMessage.value;
          const msgRecv = currentRecvMessage.value;
          currentSendMessage.value = null;
          currentRecvMessage.value = null;
          conversationStore.addMessageToConversation(currentConversationId.value!, msgSend!, msgRecv!);
          currentConversationId.value = newConversation.value.conversation_id!; // 这里将会导致 currentConversation 切换
          await conversationStore.fetchAllConversations();
          newConversation.value = null;
          console.log('done', newConvHistory, msgSend, msgRecv, currentConversationId.value);
        } else {
          // 将新消息存入 store
          if (!currentRecvMessage.value!.id!.startsWith('recv')) {
            // TODO 其它属性
            conversationStore.addMessageToConversation(
              currentConversationId.value!,
              currentSendMessage.value!,
              currentRecvMessage.value!
            );
          }
          currentSendMessage.value = null;
          currentRecvMessage.value = null;
        }
      }
    } else {
      Dialog.error({
        title: t('errors.askError'),
        content:
          wsErrorMessage != null
            ? `[${event.code}] ${t(event.reason)}: ${wsErrorMessage}`
            : `[${event.code}] ${t(event.reason)}`,
        positiveText: t('commons.withdrawMessage'),
        negativeText: t('commons.cancel'),
        onPositiveClick: () => {
          currentSendMessage.value = null;
          currentRecvMessage.value = null;
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
  saveAsMarkdown(currentConversation.value!, currentMessageListToDisplay.value);
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

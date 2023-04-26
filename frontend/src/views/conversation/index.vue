<template>
  <div
    ref="rootRef"
    :class="['flex-grow flex flex-col md:flex-row', !appStore.preference.widerConversationPage ? 'lg:w-screen-lg lg:mx-auto' : '']"
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
      :class="[
        'flex-grow flex flex-col md:px-4',
        appStore.preference.widerConversationPage ? 'md:w-4/5' : 'md:w-3/4',
      ]"
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
        
        <!-- 消息记录内容（用于全屏展示） -->
        <n-scrollbar
          v-if="currentConversationId"
          ref="historyRef"
          class="basis-0 flex-grow shrink-grow relative"
          :style="{'overflow-y': 'scroll','-webkit-overflow-scrolling': 'touch'}"
          :content-style="loadingHistory ? { height: '100%' } : { }"
        >
          <!-- 回到底部按钮 -->
          <div class="right-2 bottom-5 absolute z-20">
            <n-button
              secondary
              circle
              size="small"
              @click="scrollToBottomSmooth"
            >
              <template #icon>
                <n-icon :component="ArrowDown" />
              </template>
            </n-button>
          </div>
          <HistoryContent
            ref="historyContentRef"
            :messages="currentMessageListDisplay"
            :fullscreen="false"
            :model-name="currentConversation?.model_name || ''"
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
          <n-empty
            v-if="!currentConversation"
            :description="$t('tips.loadConversation')"
          >
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
import { ChatConversationDetail, ChatMessage } from '@/types/custom';
import { ConversationSchema } from '@/types/schema';
import { getConvMessageListFromId } from '@/utils/conversation';
import { popupNewConversationDialog } from '@/utils/renders';
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

// const currentAvaliableAskCountsTip = computed(() => {
//   let result = '';
//   if (userStore.user?.available_ask_count != -1)
//     result += `${t('commons.availableAskCount')}: ${getCountTrans(userStore.user?.available_ask_count!)}   `;
//   if (currentConversation.value && currentConversation.value.model_name === 'gpt-4' && userStore.user?.available_gpt4_ask_count != -1)
//     result += `${t('commons.availableGPT4AskCount')}: ${getCountTrans(userStore.user?.available_gpt4_ask_count!)}`;
//   return result;
// });

const newConversation = ref<ConversationSchema | null>(null);
const currentConversationId = ref<string | null>(null);
const currentConversation = computed<ConversationSchema>(() => {
  if (newConversation.value?.conversation_id === currentConversationId.value) return newConversation.value;
  const conv = conversationStore.conversations?.find((conversation: ConversationSchema) => {
    return conversation.conversation_id == currentConversationId.value;
  });
  return conv;
});

const inputValue = ref('');
const currentActiveMessageSend = ref<ChatMessage | null>(null);
const currentActiveMessageRecv = ref<ChatMessage | null>(null);
const currentMessageListDisplay = computed(() => {
  const conversationId = currentConversationId.value;
  if (!conversationId) return [];
  // const _ensure_conv = conversationStore.conversationDetailMap[props.conversationId];
  let result = getConvMessageListFromId(conversationId);
  if (currentActiveMessages.value.length > 0) {
    result = result.concat(currentActiveMessages.value);
  }
  return result;
});

// 从 store 中获取当前对话最新消息的 id
const currentNode = computed<string | undefined>(() => {
  if (currentConversation.value?.conversation_id)
    return conversationStore.conversationDetailMap[currentConversation.value?.conversation_id]?.current_node;
  else return undefined;
});

// 实际的 currentMessageList，加上当前正在发送的消息
const currentActiveMessages = computed<Array<ChatMessage>>(() => {
  const result: ChatMessage[] = [];
  if (currentActiveMessageSend.value && result.findIndex((message) => message.id === currentActiveMessageSend.value?.id) === -1)
    result.push(currentActiveMessageSend.value);
  if (currentActiveMessageRecv.value && result.findIndex((message) => message.id === currentActiveMessageRecv.value?.id) === -1)
    result.push(currentActiveMessageRecv.value);
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
  return loadingBar.value || currentConversationId.value == null || inputValue.value === null || inputValue.value.trim() == '';
});

const makeNewConversation = () => {
  if (newConversation.value) return;
  popupNewConversationDialog(async (title: string, model_name: any) => {
    // console.log(title, model_name);
    newConversation.value = {
      conversation_id: 'new_conversation',
      // 默认标题格式：MMDD - username
      title: title || `New Chat ${new Date().toLocaleString()} - ${userStore.user?.username}`,
      model_name: model_name || 'text-davinci-002-render-sha',
      create_time: new Date().toISOString(), // 仅用于当前排序到顶部
    };
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
  historyRef.value.scrollTo({ left: 0, top: historyRef.value.$refs.scrollbarInstRef.contentRef.scrollHeight, behavior: 'smooth' });
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

  const askInfo: AskInfo = { message };
  if (newConversation.value) {
    askInfo.new_title = newConversation.value.title;
    askInfo.model_name = newConversation.value.model_name;
  } else {
    askInfo.conversation_id = currentConversation.value!.conversation_id;
    askInfo.parent_id = currentNode.value!;
  }

  // 使用临时的随机 id 保持当前更新的两个消息
  const random_strid = Math.random().toString(36).substring(2, 16);
  currentActiveMessageSend.value = {
    id: `send_${random_strid}`,
    message,
    author_role: 'user',
    parent: currentNode.value,
    children: [`recv_${random_strid}`],
  };
  currentActiveMessageRecv.value = {
    id: `recv_${random_strid}`,
    message: '',
    author_role: 'assistent',
    parent: `send_${random_strid}`,
    children: [],
    typing: true,
    model_slug: currentConversation.value?.model_name,
  };
  const wsUrl = getAskWebsocketApiUrl();
  let wsErrorMessage: string | null = null;
  console.log('Connecting to', wsUrl, askInfo);
  const webSocket = new WebSocket(wsUrl);

  webSocket.onopen = (_event: Event) => {
    // console.log('WebSocket connection is open', askInfo);
    webSocket.send(JSON.stringify(askInfo));
  };

  webSocket.onmessage = (event: MessageEvent) => {
    const reply = JSON.parse(event.data);
    // console.log('Received message from server:', reply);
    if (!reply.type) return;
    if (reply.type === 'waiting') {
      // 等待回复
      canAbort.value = false;
      currentActiveMessageRecv.value!.message = t(reply.tip);
    } else if (reply.type === 'queueing') {
      // 正在排队
      canAbort.value = true;
      currentActiveMessageRecv.value!.message = t(reply.tip);
      // if (reply.waiting_count) {
      //   currentActiveMessageRecv.value!.message += `(${reply.waiting_count})`;
      // }
    } else if (reply.type === 'message') {
      // console.log(reply)
      hasGotReply = true;
      currentActiveMessageRecv.value!.message = reply.message;
      currentActiveMessageRecv.value!.id = reply.parent_id;
      currentActiveMessageRecv.value!.model_slug = reply.model_name;
      if (newConversation.value) {
        newConversation.value.model_name = reply.model_name;
        if (newConversation.value.conversation_id !== reply.conversation_id) newConversation.value.conversation_id = reply.conversation_id;
        if (currentConversationId.value !== newConversation.value.conversation_id) {
          currentConversationId.value = newConversation.value.conversation_id!;
        }
      }
      canAbort.value = true;
    } else if (reply.type === 'error') {
      currentActiveMessageRecv.value!.message = `${t(reply.tip)}: ${reply.message}}`;
      console.error(reply.tip, reply.message);
      if (reply.message) {
        wsErrorMessage = reply.message;
      }
    }
    if (autoScrolling.value) scrollToBottom();
  };

  webSocket.onclose = async (event: CloseEvent) => {
    aborter = null;
    canAbort.value = false;
    currentActiveMessageRecv.value!.typing = false;
    console.log('WebSocket connection is closed', event, isAborted.value);
    if (isAborted.value || event.code === 1000) {
      // 正常关闭
      if (hasGotReply) {
        if (newConversation.value) {
          // 解析 ISO string 为 小数时间戳
          const create_time = new Date(newConversation.value.create_time!).getTime() / 1000;
          const newConvDetail = {
            id: currentConversationId.value,
            title: newConversation.value!.title,
            model_name: newConversation.value!.model_name,
            create_time,
            mapping: {},
            current_node: null,
          } as ChatConversationDetail;
          conversationStore.$patch({
            conversationDetailMap: {
              [newConversation.value.conversation_id!]: newConvDetail,
            },
          });
          const msgSend = currentActiveMessageSend.value;
          const msgRecv = currentActiveMessageRecv.value;
          currentActiveMessageSend.value = null;
          currentActiveMessageRecv.value = null;
          conversationStore.addMessageToConversation(currentConversationId.value, msgSend, msgRecv);
          currentConversationId.value = newConversation.value.conversation_id!; // 这里将会导致 currentConversation 切换
          await conversationStore.fetchAllConversations();
          newConversation.value = null;
          console.log('done', newConvDetail, msgSend, msgRecv, currentConversationId.value);
        } else {
          // 将新消息存入 store
          if (!currentActiveMessageRecv.value!.id.startsWith('recv')) {
            // TODO 其它属性
            conversationStore.addMessageToConversation(currentConversationId.value, currentActiveMessageSend.value!, currentActiveMessageRecv.value!);
          }
          currentActiveMessageSend.value = null;
          currentActiveMessageRecv.value = null;
        }
      }
    } else {
      Dialog.error({
        title: t('errors.askError'),
        content: wsErrorMessage != null ? `[${event.code}] ${t(event.reason)}: ${wsErrorMessage}` : `[${event.code}] ${t(event.reason)}`,
        positiveText: t('commons.withdrawMessage'),
        negativeText: t('commons.cancel'),
        onPositiveClick: () => {
          currentActiveMessageSend.value = null;
          currentActiveMessageRecv.value = null;
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
  saveAsMarkdown(currentConversation.value, currentMessageListDisplay.value);
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

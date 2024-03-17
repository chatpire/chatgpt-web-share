<template>
  <n-layout
    ref="rootRef"
    has-sider
    :class="['h-full', !appStore.preference.widerConversationPage ? 'lg:w-screen-lg lg:mx-auto' : '']"
  >
    <!-- 左栏 -->
    <n-layout-sider
      v-model:collapsed="foldLeftBar"
      :native-scrollbar="false"
      :collapsed-width="0"
      collapse-mode="transform"
      trigger-style="top: 27px; right: -26px;"
      collapsed-trigger-style="top: 27px; right: -26px;"
      bordered
      show-trigger="arrow-circle"
      :width="280"
      class="h-full"
    >
      <LeftBar
        v-model:value="currentConversationId"
        :class="['h-full pt-4 px-4 box-border mb-4 overflow-hidden flex flex-col space-y-4']"
        :loading="loadingAsk"
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
          <div class="right-3 bottom-3 absolute z-20">
            <n-button secondary circle size="small" @click="scrollToBottomSmooth">
              <template #icon>
                <n-icon :component="ArrowDown" />
              </template>
            </n-button>
          </div>
          <HistoryContent
            ref="historyContentRef"
            v-model:can-continue="canContinue"
            :conversation-id="currentConversationId"
            :extra-messages="currentActiveMessages"
            :fullscreen="false"
            :show-tips="showFullscreenTips"
            :loading="loadingHistory"
          />
          <div class="h-14" />
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
              <n-button secondary @click="makeNewConversation">
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
          :can-continue="!loadingAsk && canContinue"
          :send-disabled="sendDisabled"
          :upload-mode="uploadMode"
          :upload-disabled="loadingAsk"
          @abort-request="abortRequest"
          @continue-generating="continueGenerating"
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
import { useStorage } from '@vueuse/core';
import { NButton, NIcon, useThemeVars } from 'naive-ui';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { getArkoseInfo } from '@/api/arkose';
import { getAskWebsocketApiUrl } from '@/api/chat';
import { generateConversationTitleApi, setConversationTitleApi } from '@/api/conv';
import { useAppStore, useConversationStore, useFileStore, useUserStore } from '@/store';
import { NewConversationInfo } from '@/types/custom';
import {
  AskRequest,
  AskResponse,
  BaseChatMessage,
  BaseConversationHistory,
  BaseConversationSchema,
  OpenaiWebChatMessageMetadataAttachment,
  OpenaiWebChatMessageMultimodalTextContentImagePart,
} from '@/types/schema';
import { getArkoseToken } from '@/utils/arkose';
import { screenWidthGreaterThan } from '@/utils/media';
import { popupNewConversationDialog } from '@/utils/renders';
// import { popupNewConversationDialog } from '@/utils/renders';
import { Dialog, LoadingBar, Message } from '@/utils/tips';
import HistoryContent from '@/views/conversation/components/HistoryContent.vue';
import InputRegion from '@/views/conversation/components/InputRegion.vue';
import LeftBar from '@/views/conversation/components/LeftBar.vue';

import { saveAsMarkdown } from './utils/export';
import { buildTemporaryMessage, modifiyTemporaryMessageContent } from './utils/message';

const themeVars = useThemeVars();

const { t } = useI18n();

const gtmd = screenWidthGreaterThan('md');

const rootRef = ref();
const historyRef = ref();
const userStore = useUserStore();
const appStore = useAppStore();
const fileStore = useFileStore();
const conversationStore = useConversationStore();

const loadingAsk = ref(false);
const loadingHistory = ref<boolean>(false);
const autoScrolling = useStorage('autoScrolling', true);

const isAborted = ref<boolean>(false);
const canAbort = ref<boolean>(false);
const canContinue = ref<boolean>(false);
const foldLeftBar = useStorage('foldLeftBar', false);
let aborter: (() => void) | null = null;

const hasNewConversation = ref<boolean>(false);
const currentConversationId = ref<string | null>(null);
const isCurrentNewConversation = computed<boolean>(() => {
  // return currentConversationId.value === conversationStore.newConversation?.conversation_id;
  return currentConversationId.value?.startsWith('new_conversation') || false;
});
const currentConversation = computed<BaseConversationSchema | null>(() => {
  if (isCurrentNewConversation.value) return conversationStore.newConversation;
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

const uploadMode = computed(() => {
  const disableUploading = userStore.userInfo?.setting.openai_web.disable_uploading;
  if (disableUploading) return null;
  if (
    currentConversation.value?.source === 'openai_web' &&
    currentConversation.value.current_model == 'gpt_4_code_interpreter'
  )
    return 'legacy_code_interpreter';
  else if (currentConversation.value?.source === 'openai_web' && currentConversation.value.current_model == 'gpt_4')
    return 'all';
  else return null;
});

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
  if (loadingAsk.value || !key) return;
  loadingAsk.value = true;
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
      loadingAsk.value = false;
      loadingHistory.value = false;
      LoadingBar.finish();
    });
};

const sendDisabled = computed(() => {
  return (
    loadingAsk.value ||
    currentConversationId.value == null ||
    inputValue.value === null ||
    inputValue.value.trim() == ''
  );
});

const makeNewConversation = () => {
  if (hasNewConversation.value) return;
  popupNewConversationDialog(async (newConversationInfo: NewConversationInfo) => {
    if (!newConversationInfo.source || !newConversationInfo.model) return;
    if (newConversationInfo.source == 'openai_api')
      newConversationInfo.title = newConversationInfo.title || `New Chat (${t('models.' + newConversationInfo.model)})`;
    if (newConversationInfo.openaiWebPlugins && newConversationInfo.model !== 'gpt_4_plugins') {
      newConversationInfo.openaiWebPlugins = null;
    }
    console.log('makeNewConversation', newConversationInfo);
    conversationStore.createNewConversation(newConversationInfo);
    currentConversationId.value = conversationStore.newConversation!.conversation_id!;
    hasNewConversation.value = true;
    appStore.lastSelectedSource = newConversationInfo.source;
    appStore.lastSelectedModel = newConversationInfo.model;
  });
};

const abortRequest = () => {
  if (aborter == null || !canAbort.value) return;
  aborter();
  aborter = null;
};

const continueGenerating = () => {
  inputValue.value = ':continue';
  sendMsg();
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
  if (sendDisabled.value || loadingAsk.value || currentConvHistory.value == null) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }

  LoadingBar.start();
  loadingAsk.value = true;
  canContinue.value = false;
  const text = inputValue.value;
  inputValue.value = '';

  canAbort.value = false;
  isAborted.value = false;
  let hasGotReply = false;

  // 唤起 arkose
  const { data: arkoseInfo } = await getArkoseInfo();

  // 处理附件
  let attachments = null as OpenaiWebChatMessageMetadataAttachment[] | null;
  if (uploadMode.value !== null && fileStore.uploadedFileInfos.length > 0) {
    attachments = fileStore.uploadedFileInfos
      .filter((info) => info.openai_web_info && info.openai_web_info.file_id)
      .map((info) => {
        const result = {
          id: info.openai_web_info!.file_id!,
          name: info.original_filename,
          size: info.size,
          mimeType: info.content_type,
        } as OpenaiWebChatMessageMetadataAttachment;
        if (info.extra_info && info.extra_info.height !== undefined) {
          result.height = info.extra_info.height;
          result.width = info.extra_info.width;
        }
        return result;
      });
  }

  // 处理 gpt-4 图片
  let multimodalImages = null;
  if (uploadMode.value === 'all') {
    multimodalImages = fileStore.uploadedFileInfos
      .filter((info) => info.openai_web_info && info.openai_web_info.file_id && info.content_type?.startsWith('image/'))
      .map((info) => {
        const fileId = info.openai_web_info!.file_id!;
        const { width, height } = info.extra_info || {};
        return {
          asset_pointer: `file-service://${fileId}`,
          width,
          height,
          size_bytes: info.size,
        } as OpenaiWebChatMessageMultimodalTextContentImagePart;
      });
  }

  // 使用临时的随机 id 保持当前更新的两个消息
  if (text == ':continue') {
    currentSendMessage.value = null;
    currentRecvMessages.value = [];
  } else {
    currentSendMessage.value = buildTemporaryMessage(
      currentConversation.value!.source,
      'user',
      text,
      currentConvHistory.value?.current_node,
      currentConversation.value!.current_model!,
      attachments,
      multimodalImages
    );
    currentRecvMessages.value = [
      buildTemporaryMessage(
        currentConversation.value!.source,
        'assistant',
        '...',
        currentSendMessage.value.id,
        currentConversation.value!.current_model!
      ),
    ];
  }

  let arkoseToken = null as string | null;
  if (arkoseInfo.enabled) {
    const url = arkoseInfo.url;
    try {
      arkoseToken = await getArkoseToken(url);
      console.log('Get arkose token', arkoseToken);
    } catch (err: any) {
      console.error('Failed to get Arkose token', err);
      Dialog.error({
        title: t('errors.arkoseError'),
        content: t('errors.arkoseTokenError'),
      });
      // return;
    }
  }

  const askRequest: AskRequest = {
    new_conversation: isCurrentNewConversation.value,
    source: currentConversation.value!.source,
    model: currentConversation.value!.current_model!,
    text_content: text,
    openai_web_plugin_ids:
      currentConvHistory.value!.metadata?.source === 'openai_web'
        ? currentConvHistory.value!.metadata?.plugin_ids
        : undefined,
    openai_web_attachments: attachments || undefined,
    openai_web_multimodal_image_parts: multimodalImages || undefined,
    arkose_token: arkoseToken,
  };
  if (conversationStore.newConversation) {
    askRequest.new_title = conversationStore.newConversation.title || ''; // 这里可能为空串，表示需要生成标题
  } else {
    askRequest.conversation_id = currentConversationId.value!;
    askRequest.parent = currentConvHistory.value.current_node;
  }

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
      currentRecvMessages.value![0].content = modifiyTemporaryMessageContent(
        currentRecvMessages.value![0],
        t(response.tip || 'tips.waiting')
      );
    } else if (response.type === 'queueing') {
      // 正在排队
      canAbort.value = true;
      currentRecvMessages.value![0].content = modifiyTemporaryMessageContent(
        currentRecvMessages.value![0],
        t(response.tip || 'tips.queueing')
      );
    } else if (response.type === 'message') {
      if (!hasGotReply) {
        currentRecvMessages.value = [];
        hasGotReply = true;
      }
      const message = response.message as BaseChatMessage;
      if (message.role == 'user') {
        console.log('got message', message);
        currentSendMessage.value = message;
      } else {
        if (message.title != null) {
          currentConvHistory.value!.title = message.title;
          return;
        }
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
      // TODO Message error
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
        let allNewMessages = [] as BaseChatMessage[];
        if (currentSendMessage.value) {
          allNewMessages = [currentSendMessage.value] as BaseChatMessage[];
        }
        for (const msg of currentRecvMessages.value) {
          allNewMessages.push(msg);
        }

        // 更新对话信息，恢复正常状态
        if (isCurrentNewConversation.value) {
          // 尝试生成标题或保存标题
          if (
            askRequest.source == 'openai_web' &&
            (askRequest.new_title == undefined || askRequest.new_title.length == 0)
          ) {
            if (currentConvHistory.value!.title == undefined || currentConvHistory.value!.title.length == 0) {
              const lastRecvMessageId = allNewMessages[allNewMessages.length - 1].id;
              console.log('try to generate conversation title', respConversationId, lastRecvMessageId);
              try {
                const response = await generateConversationTitleApi(respConversationId!, lastRecvMessageId);
                currentConvHistory.value!.title = response.data;
              } catch (err) {
                console.error('Failed to generate conversation title', err);
              }
            } else {
              // 自动生成了标题，更新到数据库
              const title = currentConvHistory.value!.title;
              try {
                console.log('update title', respConversationId, title);
                await setConversationTitleApi(respConversationId!, title);
              } catch (err) {
                console.error('Failed to set conversation title', err);
              }
            }
          }

          const newConvHistory = {
            _id: respConversationId!,
            source: askRequest.source,
            title: currentConvHistory.value!.title,
            current_model: currentConvHistory.value!.current_model,
            create_time: currentConvHistory.value!.create_time,
            update_time: currentConvHistory.value!.update_time,
            metadata: currentConvHistory.value!.metadata,
            mapping: {},
            current_node: '',
          } as BaseConversationHistory;
          // conversationStore.$patch({
          //   conversationHistoryMap: {
          //     [respConversationId!]: newConvHistory,
          //   },
          // });
          conversationStore.conversationHistoryMap[respConversationId!] = newConvHistory;
        }
        conversationStore.addMessagesToConversation(respConversationId!, allNewMessages);
        currentSendMessage.value = null;
        currentRecvMessages.value = [];
        currentConversationId.value = respConversationId!; // 这里将会导致 currentConversation 切换

        // 清除附件
        fileStore.clear();

        await conversationStore.fetchAllConversations();
        conversationStore.removeNewConversation();
        hasNewConversation.value = false;
        console.log('done', allNewMessages, currentConversationId.value);
      }
    } else {
      let content = '';
      if (wsErrorMessage != null) {
        if (wsErrorMessage.tip) {
          content = t(wsErrorMessage.tip) + ' ';
        }
        content += wsErrorMessage.error_detail || t('errors.unknown');
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
    loadingAsk.value = false;
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

<template>
  <div class="h-full" ref="rootRef">
    <!-- 类似聊天室，左边栏是对话列表，右边栏是聊天窗口，使用naive-ui -->
    <div class="h-full pb-6 flex flex-col md:flex-row md:space-x-4">
      <!-- 左栏 -->
      <div class="md:w-1/4 md:min-w-1/4 w-full flex flex-col space-y-4 md:overflow-y-auto">
        <StatusCard />
        <n-card class="max-h-full" content-style="padding: 4px;">
          <div class="flex box-content m-2" v-if="!newConversation">
            <n-button secondary strong type="primary" class="flex-1" @click="makeNewConversation" :disabled="loading">
              <template #icon>
                <n-icon class="">
                  <Add />
                </n-icon>
              </template>
              {{ $t("commons.newConversation") }}
            </n-button>
          </div>
          <n-menu ref="menuRef" :disabled="loading" :options="menuOptions" :root-indent="18" v-model:value="currentConversationId"></n-menu>
        </n-card>
      </div>
      <!-- 右栏 -->
      <n-card class="md:w-3/4" :bordered="true" :class="{ 'h-90%': !!currentConversationId, 'h-98%': !currentConversationId || loading }"
        content-style="padding: 0; display: flex; flex-direction: column; height: 100%;">
        <!-- 上半部分 -->
        <div class="flex-1 overflow-x-hidden h-full">
          <n-scrollbar ref="historyRef" v-if="newConversation || currentMessageListDisplay.length != 0">
            <!-- 消息记录内容（用于全屏展示） -->
            <div ref="historyContentRef" id="print-content" class="flex flex-col h-full" @keyup.esc="toggleFullscreenHistory(true)" tabindex="0"
              style="outline:none;">
              <!-- 消息记录 -->
              <div class="flex justify-center py-4 px-4 max-w-full" :style="{ backgroundColor: themeVars.baseColor }">
                <n-text>{{ $t("commons.currentConversationModel") }}: {{ getModelNameTrans(currentConversation?.model_name) }}</n-text>
              </div>
              <MessageRow :message="message" v-for="message in currentMessageListDisplay" :key="message.id" />
            </div>
          </n-scrollbar>
          <!-- 未选中对话 -->
          <div v-else-if="!currentConversationId" class="flex flex-col justify-center h-full" :style="{ backgroundColor: themeVars.cardColor }">
            <n-empty v-if="!currentConversation" :description="$t('tips.loadConversation')">
              <template #icon>
                <n-icon>
                  <ChatboxEllipses />
                </n-icon>
              </template>
              <template #extra>
                <n-button @click="makeNewConversation">
                  {{ $t("tips.newConversation") }}
                </n-button>
              </template>
            </n-empty>
          </div>
          <!-- 加载消息记录中 -->
          <div v-else-if="loading" class="flex flex-col justify-center h-full" :style="{ backgroundColor: themeVars.cardColor }">
            <n-empty :description="$t('tips.loading')">
              <template #icon>
                <n-spin size="medium" />
              </template>
            </n-empty>
          </div>
        </div>
        <!-- 下半部分 -->
        <div class="flex flex-col relative" :style="{ height: inputHeight }">
          <n-divider />
          <div class="absolute left-0 -top-8 ml-1 space-x-1">
            <!-- 展开/收起按钮 -->
            <n-button @click="toggleInputExpanded" circle secondary size="small">
              <template #icon>
                <n-icon :component="inputExpanded ? KeyboardDoubleArrowDownRound : KeyboardDoubleArrowUpRound"></n-icon>
              </template>
            </n-button>
          </div>
          <!-- 工具栏 -->
          <div class="flex flex-row space-x-2 py-2 justify-center">
            <n-button secondary type="info" size="small" @click="showFullscreenHistory">
              <template #icon>
                <n-icon :size="22">
                  <FullscreenRound />
                </n-icon>
              </template>
            </n-button>
            <n-button secondary type="primary" size="small" @click="exportToMarkdownFile">
              <template #icon>
                <n-icon>
                  <LogoMarkdown />
                </n-icon>
              </template>
            </n-button>
            <n-button secondary type="warning" size="small" @click="exportToPdfFile">
              <template #icon>
                <n-icon>
                  <Print />
                </n-icon>
              </template>
            </n-button>
          </div>
          <!-- 输入框 -->
          <n-input v-model:value="inputValue" class="flex-1" type="textarea" :bordered="false" :placeholder="$t('tips.sendMessage')"
            @keydown.shift.enter="shortcutSendMsg" />
          <div class="m-2 flex flex-row justify-between">
            <n-text depth="3" class="hidden sm:block">
              {{ currentAvaliableAskCountsTip }}
            </n-text>
            <n-button :disabled="sendDisabled" @click="sendMsg" class="" type="primary" size="small">
              {{ $t("commons.send") }}
              <template #icon><n-icon>
                  <Send />
                </n-icon></template>
            </n-button>
          </div>
        </div>
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useConversationStore, useUserStore } from '@/store';
import { ConversationSchema } from '@/types/schema';
import { ref, computed, watch, h, triggerRef } from 'vue';
import { LoadingBar, Dialog, Message } from '@/utils/tips';

import StatusCard from './components/StatusCard.vue';
import MessageRow from './components/MessageRow.vue';

import { ChatConversationDetail, ChatMessage } from '@/types/custom';
import { AskInfo, getAskWebsocketApiUrl } from '@/api/chat';

import { useI18n } from 'vue-i18n';
import { NDropdown, NEllipsis, NButton, NIcon } from 'naive-ui';
import { Send, ChatboxEllipses, LogoMarkdown, Add, Print } from '@vicons/ionicons5';
import { KeyboardDoubleArrowUpRound, KeyboardDoubleArrowDownRound, FullscreenRound, PhotoRound } from '@vicons/material';
import { popupChangeConversationTitleDialog, dropdownRenderer, popupNewConversationDialog, getCountTrans, getModelNameTrans } from '@/utils/renders';

import { useThemeVars } from "naive-ui"
import { saveAs } from 'file-saver';
import md from "@/utils/markdown";

const themeVars = useThemeVars()

const { t } = useI18n();

const rootRef = ref();
const menuRef = ref(null);
const historyRef = ref();
const userStore = useUserStore();
const conversationStore = useConversationStore();

const inputExpanded = ref<Boolean>(false);
const inputHeight = computed(() => inputExpanded.value ? '50vh' : '24vh');
const toggleInputExpanded = () => {
  inputExpanded.value = !inputExpanded.value;
};

const currentAvaliableAskCountsTip = computed(() => {
  let result = '';
  if (userStore.user?.available_ask_count != -1)
    result += `${t('commons.availableAskCount')}: ${getCountTrans(userStore.user?.available_ask_count!)}   `;
  if (currentConversation.value && currentConversation.value.model_name === 'gpt-4' && userStore.user?.available_gpt4_ask_count != -1) result += `${t('commons.availableGPT4AskCount')}: ${getCountTrans(userStore.user?.available_gpt4_ask_count!)}`;
  return result;
});

const newConversation = ref<ConversationSchema | null>(null);
const currentConversationId = ref<string | null>(null);
const currentConversation = computed<ConversationSchema | any>(() => {
  if (newConversation.value?.conversation_id === currentConversationId.value) return newConversation.value;
  const conv = conversationStore.conversations?.find((conversation: ConversationSchema) => {
    return conversation.conversation_id == currentConversationId.value;
  });
  return conv;
});

const inputValue = ref('');
const loading = ref(false);
const currentActiveMessageSend = ref<ChatMessage | null>(null);
const currentActiveMessageRecv = ref<ChatMessage | null>(null);

// 从 store 中获取对话列表
const menuOptions = computed(() => {
  // 根据 created_time 降序排序
  const sorted_conversations = conversationStore.conversations?.sort((a: ConversationSchema, b: ConversationSchema) => {
    // return a.create_time - b.create_time;
    if (!a.create_time) return -1;
    if (!b.create_time) return 1;
    const date_a = new Date(a.create_time), date_b = new Date(b.create_time);
    return date_b.getTime() - date_a.getTime();
  });
  const results = sorted_conversations?.map((conversation: ConversationSchema) => {
    return {
      label: () =>
        h(NEllipsis, null, { default: () => conversation.title }),
      key: conversation.conversation_id,
      disabled: loading.value == true,
      extra: () => dropdownRenderer(conversation, handleDeleteConversation, handleChangeConversationTitle)
    }
  });
  if (newConversation.value) {
    results?.unshift({
      label: newConversation.value.title,
      key: newConversation.value.conversation_id,
      disabled: loading.value == true,
    });
  }
  return results;
});


const handleDeleteConversation = (conversation_id: string | undefined) => {
  if (!conversation_id) return;
  const d = Dialog.info({
    title: t("commons.confirmDialogTitle"),
    content: t("tips.deleteConversation"),
    positiveText: t("commons.confirm"),
    negativeText: t("commons.cancel"),
    onPositiveClick: () => {
      d.loading = true;
      return new Promise((resolve) => {
        conversationStore.deleteConversation(conversation_id).then(() => {
          Message.success(t("tips.deleteConversationSuccess"));
          if (currentConversationId.value == conversation_id)
            currentConversationId.value = null;
        }).catch(() => {
          Message.error(t("tips.deleteConversationFailed"));
        }).finally(() => {
          d.loading = false;
          resolve(true);
        })
      });
    }
  });
}


const handleChangeConversationTitle = (conversation_id: string | undefined) => {
  if (!conversation_id) return;
  popupChangeConversationTitleDialog(
    conversation_id,
    async (title: string) => {
      await conversationStore.changeConversationTitle(conversation_id, title);
    },
    () => { Message.success(t("tips.changeConversationTitleSuccess")); },
    () => { Message.error(t("tips.changeConversationTitleFailed")); }
  );
}

// 从 store 中获取当前对话最新消息的 id
const currentNode = computed<string | undefined>(() => {
  return conversationStore.conversationDetailMap[currentConversation.value?.conversation_id]?.current_node;
})

// 从 store 中获取当前对话的消息列表，将链表转换为数组
// const currentMessageList = computed<Array<ChatMessage>>(() => {

//   console.log("currentMessageList", result);
//   return result;
// });

// 实际的 currentMessageList，加上当前正在发送的消息
const currentMessageListDisplay = computed<Array<ChatMessage>>(() => {
  const result = [];
  const conversation_id = currentConversation.value?.conversation_id;
  const conv = conversationStore.conversationDetailMap[conversation_id];
  if (conv) {
    let x = conv.current_node;
    while (!!x) {
      if (conv.mapping[x].message)
        result.push(conv.mapping[x]);
      x = conv.mapping[x].parent;
    }
    result.reverse();
  }
  if (currentActiveMessageSend.value && result.findIndex((message) => message.id === currentActiveMessageSend.value?.id) === -1)
    result.push(currentActiveMessageSend.value);
  if (currentActiveMessageRecv.value && result.findIndex((message) => message.id === currentActiveMessageRecv.value?.id) === -1)
    result.push(currentActiveMessageRecv.value);
  return result;
});


watch(currentConversationId, (newVal, oldVal) => {
  if (newVal != "new_conversation") {
    handleChangeConversation(newVal)
  }
});

const handleChangeConversation = (key: string | null) => {
  if (loading.value || !key) return;
  loading.value = true;
  LoadingBar.start();
  conversationStore.fetchConversationHistory(key).then(() => {
    // console.log(conversationStore.conversationDetailMap);
  }).catch((err: any) => {
    console.log(err);
  }).finally(() => {
    loading.value = false;
    LoadingBar.finish();
  })
};


const sendDisabled = computed(() => {
  return loading.value || currentConversationId.value == null || inputValue.value === null || inputValue.value.trim() == '';
});


const makeNewConversation = () => {
  if (newConversation.value) return;
  popupNewConversationDialog(
    async (title: string, model_name: any) => {
      console.log(title, model_name);
      newConversation.value = {
        conversation_id: "new_conversation",
        // 默认标题格式：MMDD - username
        title: title || `New Chat ${new Date().toLocaleString()} - ${userStore.user?.username}`,
        model_name: model_name || 'text-davinci-002-render-sha',
        create_time: new Date().toISOString(),  // 仅用于当前排序到顶部
      };
      currentConversationId.value = "new_conversation";
    },
  )
}

const shortcutSendMsg = (e: KeyboardEvent) => {
  e.preventDefault();
  sendMsg();
}


const sendMsg = async () => {
  if (sendDisabled.value || loading.value) {
    return;
  }

  LoadingBar.start();
  loading.value = true;
  const message = inputValue.value;
  inputValue.value = '';

  // // 新建对话
  // const askInfo: AskInfo = { message };
  // // 继续发送
  // if (currentConversation.value?.conversation_id != null) {
  //   askInfo.conversation_id = currentConversation.value.conversation_id;
  //   askInfo.parent_id = currentNode.value!;
  // }
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
  }
  const wsUrl = getAskWebsocketApiUrl();
  let wsErrorMessage: string | null = null;
  console.log('Connecting to', wsUrl, askInfo);
  const webSocket = new WebSocket(wsUrl);

  webSocket.onopen = (event: Event) => {
    console.log('WebSocket connection is open', askInfo);
    webSocket.send(JSON.stringify(askInfo));
  };

  webSocket.onmessage = (event: MessageEvent) => {
    const reply = JSON.parse(event.data);
    // console.log('Received message from server:', reply);
    if (!reply.type) return;
    if (reply.type === 'waiting') {
      currentActiveMessageRecv.value!.message = t(reply.tip);
      if (reply.waiting_count) {
        currentActiveMessageRecv.value!.message += `(${reply.waiting_count})`;
      }
    } else if (reply.type === 'message') {
      currentActiveMessageRecv.value!.message = reply.message;
      currentActiveMessageRecv.value!.id = reply.parent_id;
      if (newConversation.value) {
        newConversation.value.conversation_id = reply.conversation_id;
        if (currentConversationId.value !== newConversation.value.conversation_id) {
          currentConversationId.value = newConversation.value.conversation_id!;
        }
      }
    } else if (reply.type === 'error') {
      currentActiveMessageRecv.value!.message = `${t(reply.tip)}: ${reply.message}}`;
      console.error(reply.tip, reply.message);
      if (reply.message) {
        wsErrorMessage = reply.message;
      }
    }
    historyRef.value.scrollTo({ left: 0, top: historyRef.value.$refs.scrollbarInstRef.contentRef.scrollHeight, behavior: 'smooth' });
  };

  webSocket.onclose = async (event: CloseEvent) => {
    currentActiveMessageRecv.value!.typing = false;
    console.log('WebSocket connection is closed', event);
    if (event.code === 1000) {  // 正常关闭        
      // 对于新对话，重新请求对话列表
      if (newConversation.value) {
        await conversationStore.fetchAllConversations();
        currentConversationId.value = newConversation.value.conversation_id!;
        // 解析 ISO string 为 小数时间戳
        const create_time = new Date(newConversation.value.create_time!).getTime() / 1000;
        conversationStore.$patch({
          conversationDetailMap: {
            [currentConversationId.value]: {
              id: currentConversationId.value,
              title: newConversation.value!.title,
              model_name: newConversation.value!.model_name,
              create_time,
              mapping: {},
              current_node: null,
            } as ChatConversationDetail,
          },
        });
        conversationStore.addMessageToConversation(currentConversationId.value, currentActiveMessageSend.value!, currentActiveMessageRecv.value!);
        newConversation.value = null;
      } else {
        // 将新消息存入 store
        if (!currentActiveMessageRecv.value!.id.startsWith('recv')) {
          // TODO 其它属性
          conversationStore.addMessageToConversation(currentConversationId.value, currentActiveMessageSend.value!, currentActiveMessageRecv.value!);
        }
      }
      currentActiveMessageSend.value = null;
      currentActiveMessageRecv.value = null;
    } else {
      Dialog.error({
        title: t('errors.askError'),
        content: wsErrorMessage != null ? `[${event.code}] ${t(event.reason)}: ${wsErrorMessage}` : `[${event.code}] ${t(event.reason)}`,
        positiveText: t('commons.withdrawMessage'),
        onPositiveClick: () => {
          currentActiveMessageSend.value = null;
          currentActiveMessageRecv.value = null;
        },
      })
    }
    await userStore.fetchUserInfo();
    LoadingBar.finish();
    loading.value = false;
  };

  webSocket.onerror = (event: Event) => {
    console.error('WebSocket error:', event);
  };
}

const exportToMarkdownFile = () => {
  if (!currentConversation.value) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }
  let content = `# ${currentConversation.value!.title}\n\n`;
  const create_time = new Date(currentConversation.value!.create_time!).toLocaleString();
  content += `Date: ${create_time}\nModel: ${getModelNameTrans(currentConversation.value!.model_name)}\n`;
  content += "generated by [ChatGPT Web Share](https://github.com/moeakwak/chatgpt-web-share)\n\n"
  content += '---\n\n';
  let index = 0;
  for (const message of currentMessageListDisplay.value) {
    if (message.author_role === 'user') {
      // 选取第一行作为标题，最多30个字符，如果有省略则加上...
      let title = message.message!.trim().split('\n')[0];
      if (title.length >= 30) {
        title = title.slice(0, 27) + '...';
      }
      content += `## ${++index}. ${title}\n\n`;
      content += `### User\n\n${message.message}\n\n`;
    } else {
      content += `### ChatGPT\n\n${message.message}\n\n`;
      content += "---\n\n";
    }
  }
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  saveAs(blob, `${currentConversation.value!.title} - ChatGPT history.md`);
}

const historyContentRef = ref();
const fullscreenHistory = ref<Boolean>(false);
const historyContentParent = ref<HTMLElement>();

const toggleFullscreenHistory = (showTips: boolean) => {
  console.log('toggleFullscreenHistory')
  // fullscreenHistory.value = !fullscreenHistory.value;
  const appElement = document.getElementById('app');
  const bodyElement = document.body;
  const historyContentElement = historyContentRef.value;
  if (fullscreenHistory.value) {
    // 将 historyContent 移动回来
    historyContentParent.value!.appendChild(historyContentElement);
    if (appElement) appElement.style.display = 'block';
  } else {
    historyContentParent.value = historyContentElement.parentElement!;
    // 移动到body child的第一个
    bodyElement.insertBefore(historyContentElement, bodyElement.firstChild);
    // 将div#app 设置为不可见
    if (appElement) {
      appElement.style.display = 'none';
    }
    historyContentElement.focus();
    if (showTips)
      Message.success(t('tips.pressEscToExitFullscreen'), {
        duration: 2000,
      });
  }
  fullscreenHistory.value = !fullscreenHistory.value;
};

const showFullscreenHistory = () => {
  if (!currentConversation.value) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }
  // focus historyContentRef
  historyContentRef.value.focus();
  toggleFullscreenHistory(true);
}

const exportToPdfFile = () => {
  if (!currentConversation.value) {
    Message.error(t('tips.pleaseSelectConversation'));
    return;
  }
  toggleFullscreenHistory(false);
  window.print();
  toggleFullscreenHistory(false);
}

// 加载对话列表
conversationStore.fetchAllConversations().then(() => {
})


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

.n-divider {
  margin-bottom: 0px !important;
  margin-top: 0px !important;
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
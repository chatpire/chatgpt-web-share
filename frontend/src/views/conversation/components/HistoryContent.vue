<template>
  <div
    id="print-content"
    ref="contentRef"
    class="flex flex-col h-full p-0"
    tabindex="0"
    style="outline: none"
    @keyup.esc="toggleFullscreenHistory(true)"
  >
    <div v-if="!props.loading" class="relative">
      <div class="flex justify-center py-4 relative" :style="{ backgroundColor: themeVars.baseColor }">
        <n-text>
          {{ $t('commons.currentConversationModel') }}:
          {{ getChatModelNameTrans(convHistory?.current_model || null) }} ({{ t(`sources.${convHistory?.source}`) }})
        </n-text>
        <n-button v-if="_fullscreen" class="absolute left-4 hide-in-print" text @click="toggleFullscreenHistory">
          <template #icon>
            <n-icon>
              <Close />
            </n-icon>
          </template>
        </n-button>
      </div>
      <div
        v-if="convOpenaiWebPluginIds && convOpenaiWebPluginIds.length > 0"
        class="flex flex-row items-center justify-center pb-4 relative"
        :style="{ backgroundColor: themeVars.baseColor }"
      >
        <n-text> {{ $t('labels.plugins') }}: </n-text>
        <div v-if="convOpenaiWebPlugins === null" class="ml-3 flex flex-row space-x-1 items-center">
          <n-spin :size="16" />
          <span>{{ $t('tips.loading') }}</span>
        </div>
        <div v-else>
          <div v-for="(plugin, i) of convOpenaiWebPlugins" :key="i" class="mx-2 flex flex-row space-x-1 items-center">
            <img v-if="plugin.manifest?.logo_url" :src="plugin.manifest?.logo_url" class="w-5 h-5">
            <span>{{ plugin.manifest?.name_for_human }}</span>
          </div>
        </div>
      </div>
      <!-- 消息记录 -->
      <MessageRow v-for="messages in filteredMessagesList" :key="messages[0].id" :messages="messages" />
    </div>
    <n-empty
      v-else
      class="h-full flex justify-center"
      :style="{ backgroundColor: themeVars.cardColor }"
      :description="$t('tips.loading')"
    >
      <template #icon>
        <n-spin size="medium" />
      </template>
    </n-empty>
  </div>
</template>

<script setup lang="ts">
import { Close } from '@vicons/ionicons5';
import { useThemeVars } from 'naive-ui';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { getOpenaiChatPluginApi } from '@/api/chat';
import { useConversationStore } from '@/store';
import { BaseChatMessage, BaseConversationHistory, OpenAIChatPlugin } from '@/types/schema';
import { getChatModelNameTrans, getMessageListFromHistory, mergeContinuousMessages } from '@/utils/chat';
import { Message } from '@/utils/tips';

import MessageRow from './MessageRow.vue';

const { t } = useI18n();

const themeVars = useThemeVars();
const conversationStore = useConversationStore();

const props = defineProps<{
  conversationId: string;
  extraMessages: BaseChatMessage[];
  fullscreen: boolean; // 初始状态下是否全屏
  showTips: boolean;
  loading: boolean;
}>();

const contentRef = ref();
const historyContentParent = ref<HTMLElement>();
const _fullscreen = ref(false);

const convHistory = computed<BaseConversationHistory | null>(() => {
  const conversationId = props.conversationId;
  if (!conversationId) return null;
  return conversationStore.conversationHistoryMap[conversationId];
});

const convOpenaiWebPluginIds = computed<string[] | null>(() => {
  if (convHistory.value?.meta && convHistory.value.meta.source === 'openai_web') {
    return convHistory.value.meta.plugin_ids || null;
  }
  return null;
});

const convOpenaiWebPlugins = ref<OpenAIChatPlugin[] | null>(null);

const rawMessages = computed<BaseChatMessage[]>(() => {
  let result = convHistory.value ? getMessageListFromHistory(convHistory.value) : [];
  result = result.concat(props.extraMessages || []);
  return result;
});

const filteredMessages = computed<BaseChatMessage[]>(() => {
  return rawMessages.value
    ? rawMessages.value.filter((message) => {
      if (message.role == 'system') return false;
      return true;
    })
    : [];
});

const filteredMessagesList = computed<BaseChatMessage[][]>(() => {
  return mergeContinuousMessages(filteredMessages.value);
});

watch(
  () => props.fullscreen,
  () => {
    toggleFullscreenHistory(props.showTips);
  }
);

watch(() => convOpenaiWebPluginIds.value, async (pluginIds) => {
  console.log(1);
  if (!pluginIds) return;
  const allRequests = pluginIds.map((pluginId) => getOpenaiChatPluginApi(pluginId));
  const results = await Promise.all(allRequests);
  console.log('convOpenaiWebPlugins', results);
  convOpenaiWebPlugins.value = results.map((result) => result.data);
}, {
  immediate: true,
});


const toggleFullscreenHistory = (showTips: boolean) => {
  // fullscreenHistory.value = !fullscreenHistory.value;
  const appElement = document.getElementById('app');
  const bodyElement = document.body;
  const historyContentElement = contentRef.value;
  if (_fullscreen.value) {
    // 将 historyContent 移动回来
    historyContentParent.value?.appendChild(historyContentElement);
    if (appElement) appElement.style.display = 'block';
  } else {
    historyContentParent.value = historyContentElement.parentElement;
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
  _fullscreen.value = !_fullscreen.value;
};

if (props.fullscreen) {
  toggleFullscreenHistory(props.showTips);
}

const focus = () => {
  contentRef.value.focus();
};

defineExpose({
  focus,
  toggleFullscreenHistory,
});
</script>

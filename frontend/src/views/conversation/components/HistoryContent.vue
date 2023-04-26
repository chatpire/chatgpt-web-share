<template>
  <div
    id="print-content"
    ref="contentRef"
    class="flex flex-col h-full"
    tabindex="0"
    style="outline: none"
    @keyup.esc="toggleFullscreenHistory(true)"
  >
    <div v-if="!props.loading">
      <!-- 消息记录 -->
      <div class="flex justify-center py-4 px-4 max-w-full relative" :style="{ backgroundColor: themeVars.baseColor }">
        <n-text>{{ $t('commons.currentConversationModel') }}: {{ getRevChatModelNameTrans(modelName as any) }}</n-text>
        <n-button v-if="_fullscreen" class="absolute left-4 hide-in-print" text @click="toggleFullscreenHistory">
          <template #icon>
            <n-icon>
              <Close />
            </n-icon>
          </template>
        </n-button>
      </div>
      <MessageRow v-for="message in messages" :key="message.id" :message="message" />
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

import { ChatMessage } from '@/types/custom';
import { getRevChatModelNameTrans } from '@/utils/chat';
import { getModelNameFromMessages } from '@/utils/conversation';
import { Message } from '@/utils/tips';

import MessageRow from './MessageRow.vue';

const { t } = useI18n();

const themeVars = useThemeVars();

const props = defineProps<{
  messages: ChatMessage[];
  modelName?: string;
  fullscreen: boolean; // 初始状态下是否全屏
  showTips: boolean;
  loading: boolean;
}>();

const contentRef = ref();
const historyContentParent = ref<HTMLElement>();
const _fullscreen = ref(false);

const modelName = computed(() => {
  if (props.modelName) {
    return props.modelName;
  } else {
    return getModelNameFromMessages(props.messages);
  }
});

watch(
  () => props.fullscreen,
  () => {
    toggleFullscreenHistory(props.showTips);
  }
);

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

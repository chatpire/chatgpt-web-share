<template>
  <div ref="contentRef" id="print-content" class="flex flex-col h-full" @keyup.esc="toggleFullscreenHistory(true)" tabindex="0" style="outline:none;">
    <div v-if="!props.loading">
      <!-- 消息记录 -->
      <div class="flex justify-center py-4 px-4 max-w-full" :style="{ backgroundColor: themeVars.baseColor }">
        <n-text>{{ $t("commons.currentConversationModel") }}: {{ getModelNameTrans(modelName as any) }}
        </n-text>
      </div>
      <MessageRow :message="message" v-for="message in messages" :key="message.id" />
    </div>
    <n-empty v-else class="h-full flex justify-center" :style="{ backgroundColor: themeVars.cardColor }" :description="$t('tips.loading')">
      <template #icon>
        <n-spin size="medium" />
      </template>
    </n-empty>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from "vue";
import { useThemeVars } from "naive-ui";
import { getModelNameTrans } from "@/utils/renders";
import { ChatMessage } from "@/types/custom";
import { Message } from "@/utils/tips";
import { useI18n } from "vue-i18n";
import MessageRow from "./MessageRow.vue";
import { useConversationStore } from "@/store";
import { getModelNameFromMessages } from "@/utils/conversation";

const conversationStore = useConversationStore();
const { t } = useI18n();

const themeVars = useThemeVars();

const props = defineProps<{
  messages: ChatMessage[];
  modelName?: string;
  fullscreen: boolean;  // 初始状态下是否全屏
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
    console.log('getModelNameFromMessages', getModelNameFromMessages(props.messages))
    return getModelNameFromMessages(props.messages);
  }
});

watch(() => props.fullscreen, () => {
  toggleFullscreenHistory(props.showTips);
});

const toggleFullscreenHistory = (showTips: boolean) => {
  console.log('toggleFullscreenHistory')
  // fullscreenHistory.value = !fullscreenHistory.value;
  const appElement = document.getElementById('app');
  const bodyElement = document.body;
  const historyContentElement = contentRef.value;
  if (_fullscreen.value) {
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
  _fullscreen.value = !_fullscreen.value;
};

if (props.fullscreen) {
  toggleFullscreenHistory(props.showTips);
}

const focus = () => {
  console.log('focus');
  contentRef.value.focus();
};

defineExpose({
  focus,
  toggleFullscreenHistory
});

</script>

<template>
  <div class="flex flex-col align-middle" :style="{ background: themeVars.baseColor }">
    <n-divider />
    <!-- 暂停按钮 -->
    <div class="flex w-full justify-center absolute -top-10">
      <n-button
        v-show="canAbort"
        secondary
        strong
        type="error"
        size="small"
        @click="emits('abort-request')"
      >
        <template #icon>
          <Stop />
        </template>
        {{ t('commons.abortRequest') }}
      </n-button>
    </div>

    <!-- 工具栏 -->
    <div class="mx-2 flex flex-row space-x-2 py-2 justify-center relative">
      <!-- 展开/收起按钮 -->
      <n-button class="absolute left-0 top-2" quaternary circle size="small" @click="toggleInputExpanded">
        <template #icon>
          <n-icon :component="inputExpanded ? KeyboardDoubleArrowDownRound : KeyboardDoubleArrowUpRound" />
        </template>
      </n-button>
      <!-- 是否启用自动滚动 -->
      <n-tooltip>
        <template #trigger>
          <n-switch v-model:value="autoScrolling" size="small" class="absolute right-2 top-3">
            <template #icon>
              A
            </template>
          </n-switch>
        </template>
        {{ $t('tips.autoScrolling') }}
      </n-tooltip>
      <n-button secondary type="info" size="small" @click="emits('show-fullscreen-history')">
        <template #icon>
          <n-icon :size="22">
            <FullscreenRound />
          </n-icon>
        </template>
      </n-button>
      <n-button secondary type="primary" size="small" @click="emits('export-to-markdown-file')">
        <template #icon>
          <n-icon>
            <LogoMarkdown />
          </n-icon>
        </template>
      </n-button>
      <n-button secondary type="warning" size="small" @click="emits('export-to-pdf-file')">
        <template #icon>
          <n-icon>
            <Print />
          </n-icon>
        </template>
      </n-button>
    </div>
    <!-- 输入框 -->
    <div class="mx-4 mb-4 flex flex-row space-x-2">
      <n-input
        ref="inputRef"
        v-model:value="inputValue"
        class="flex-1"
        type="textarea"
        :bordered="true"
        :placeholder="$t('tips.sendMessage', [appStore.preference.sendKey])"
        :autosize="{ minRows: 1 }"
        :style="inputStyle"
        @keydown="shortcutSendMsg"
      >
        <template #suffix>
          <n-button
            :disabled="sendDisabled"
            text
            class=""
            type="primary"
            size="small"
            @click="emits('send-msg')"
          >
            <template #icon>
              <n-icon> <Send /> </n-icon>
            </template>
          </n-button>
        </template>
      </n-input>
    </div>
    <!-- <div class="mb-1 mx-auto">
        <n-text depth="3" class="text-size-[0.6rem]">
          {{ currentAvaliableAskCountsTip }}
        </n-text>
      </div> -->
  </div>
</template>

<script setup lang="ts">
import { LogoMarkdown, Print, Send, Stop } from '@vicons/ionicons5';
import { FullscreenRound, KeyboardDoubleArrowDownRound, KeyboardDoubleArrowUpRound } from '@vicons/material';
import { useThemeVars } from 'naive-ui';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { useAppStore } from '@/store';

const themeVars = useThemeVars();
const appStore = useAppStore();
const { t } = useI18n();

const props = defineProps<{
  canAbort: boolean;
  sendDisabled: boolean;
  inputValue: string;
  autoScrolling: boolean;
}>();

const autoScrolling = computed({
  get() {
    return props.autoScrolling;
  },
  set(value) {
    emits('update:auto-scrolling', value);
  },
});

const inputExpanded = ref<boolean>(false);
const inputStyle = computed(() => {
  if (!inputExpanded.value)
    return {
      height: 'auto',
      maxHeight: '16vh',
    };
  return {
    height: '30vh',
  };
});

const inputValue = computed({
  get() {
    return props.inputValue;
  },
  set(value) {
    emits('update:input-value', value);
  },
});

const emits = defineEmits<{
  (e: 'abort-request'): void;
  (e: 'send-msg'): void;
  (e: 'export-to-markdown-file'): void;
  (e: 'export-to-pdf-file'): void;
  (e: 'show-fullscreen-history'): void;
  (e: 'update:auto-scrolling', value: boolean): void;
  (e: 'update:input-value', value: string): void;
}>();

const toggleInputExpanded = () => {
  inputExpanded.value = !inputExpanded.value;
};

const shortcutSendMsg = (e: KeyboardEvent) => {
  const sendKey = appStore.preference.sendKey; // "Shift+Enter" or "Ctrl+Enter" or "Enter"
  if (sendKey === 'Enter' && e.key === 'Enter' && !e.shiftKey && !e.ctrlKey && !e.isComposing) {
    e.preventDefault();
    emits('send-msg');
  } else if (sendKey === 'Shift+Enter' && e.key === 'Enter' && e.shiftKey && !e.ctrlKey) {
    e.preventDefault();
    emits('send-msg');
  } else if (sendKey === 'Ctrl+Enter' && e.key === 'Enter' && !e.shiftKey && e.ctrlKey) {
    e.preventDefault();
    emits('send-msg');
  }
};
</script>

<style>
.n-divider {
  margin-bottom: 0px !important;
  margin-top: 0px !important;
}
</style>

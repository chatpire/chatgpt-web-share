<template>
  <n-form v-model:value="model" label-align="left" label-placement="left" label-width="10rem">
    <n-form-item :label="t('commons.language')">
      <n-select v-model:value="language" :options="languageOptions" />
    </n-form-item>
    <n-form-item :label="t('commons.sendKey')" prop="sendKey">
      <n-select v-model:value="model.sendKey" :options="sendKeyOptions" />
    </n-form-item>
    <n-form-item :label="t('commons.renderUserMessageInMd')" prop="renderUserMessageInMd">
      <n-switch v-model:value="model.renderUserMessageInMd" />
    </n-form-item>
    <n-form-item :label="t('commons.codeAutoWrap')" prop="codeAutoWrap">
      <n-switch v-model:value="model.codeAutoWrap" />
    </n-form-item>
    <n-form-item :label="t('commons.widerConversationPage')" prop="widerConversationPage">
      <n-switch v-model:value="model.widerConversationPage" />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { i18n } from '@/i18n';
import { useAppStore } from '@/store';
import { Preference } from '@/store/types';

const t = i18n.global.t as any;
const appStore = useAppStore();

const props = defineProps<{
  value: Preference;
}>();

const model = ref<Preference>(props.value);

const language = computed({
  get: () => appStore.language,
  set: (value) => {
    appStore.setLanguage(value);
  },
});

const sendKeyOptions = [
  { label: 'Enter', value: 'Enter' },
  { label: 'Shift+Enter', value: 'Shift+Enter' },
  { label: 'Ctrl+Enter', value: 'Ctrl+Enter' },
];

const languageOptions = [
  { label: '简体中文', value: 'zh-CN' },
  { label: 'English', value: 'en-US' },
];

const emit = defineEmits(['update:value']);

watch(
  () => model.value,
  () => {
    emit('update:value', model.value);
  }
);
</script>

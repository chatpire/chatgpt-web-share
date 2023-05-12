<template>
  <!-- A n-form: a n-select to switch sendKey in ["Shift+Enter", "Enter", "Ctrl+Enter"] -->
  <n-form v-model:value="model" label-placement="left" label-width="auto">
    <n-form-item :label="t('commons.sendKey')" prop="sendKey">
      <n-select v-model:value="model.sendKey" :options="sendKeyOptions" />
    </n-form-item>
    <!-- n-switch for renderUserMessageInMd and codeAutoWrap -->
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
import { ref, watch } from 'vue';

import { i18n } from '@/i18n';
import { Preference } from '@/store/types';

const t = i18n.global.t as any;

const props = defineProps<{
  value: Preference;
}>();

const model = ref<Preference>(props.value);

const sendKeyOptions = [
  { label: 'Enter', value: 'Enter' },
  { label: 'Shift+Enter', value: 'Shift+Enter' },
  { label: 'Ctrl+Enter', value: 'Ctrl+Enter' },
];

const emit = defineEmits(['update:value']);

watch(
  () => model.value,
  () => {
    emit('update:value', model.value);
  }
);
</script>

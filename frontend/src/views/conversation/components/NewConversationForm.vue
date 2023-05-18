<template>
  <n-form :label-placement="'left'" :label-align="'left'" label-width="100px">
    <n-form-item :label="t('labels.title')">
      <n-input v-model:value="newConversationInfo.title" />
    </n-form-item>
    <n-form-item :label="t('labels.type')">
      <n-select v-model:value="newConversationInfo.type" :options="availableChatSourceTypes" />
    </n-form-item>
    <n-form-item :label="t('labels.model')">
      <n-select v-model:value="newConversationInfo.model" :options="availableModels" />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { SelectOption } from 'naive-ui';
import { computed, ref, watch } from 'vue';

import { i18n } from '@/i18n';
import { useUserStore } from '@/store';
import { NewConversationInfo } from '@/types/custom';

const t = i18n.global.t as any;

const userStore = useUserStore();


const availableChatSourceTypes = computed<SelectOption[]>(() => {
  if (!userStore.user) {
    return [];
  }
  return [
    {label: t('labels.rev'), value: 'rev', disabled: !userStore.user.setting.rev.allow_to_use},
    {label: t('labels.api'), value: 'api', disabled: !userStore.user.setting.api.allow_to_use},
  ];
});

const newConversationInfo = ref<NewConversationInfo>({
  title: null,
  type: availableChatSourceTypes.value.length > 0 ? availableChatSourceTypes.value[0].value as string : null,
  model: null,
});

const availableModels = computed<SelectOption[]>(() => {
  if (!userStore.user) {
    return [];
  }
  if (newConversationInfo.value.type === 'rev') {
    return userStore.user.setting.rev.available_models.map((model) => ({
      label: t(`models.${model}`),
      value: model,
    }));
  } else {
    return userStore.user.setting.api.available_models.map((model) => ({
      label: t(`models.${model}`),
      value: model,
    }));
  }
});

const emits = defineEmits<{
  (e: 'input', newConversationInfo: NewConversationInfo): void;
}>();

watch(
  () => {
    return {
      title: newConversationInfo.value.title,
      type: newConversationInfo.value.type,
      model: newConversationInfo.value.model,
    } as NewConversationInfo;
  },
  (newVal, _prev) => {
    console.log('newConversationInfo', newVal);
    emits('input', newVal);
  },
  { immediate: true }
);

watch(
  () => newConversationInfo.value.type,
  () => {
    newConversationInfo.value.model = null;
  }
);
</script>

<template>
  <n-form :label-placement="'left'" :label-align="'left'" label-width="100px">
    <n-form-item :label="t('labels.title')">
      <n-input v-model:value="newConversationInfo.title" />
    </n-form-item>
    <n-form-item :label="t('labels.source')">
      <n-select v-model:value="newConversationInfo.source" :options="availableChatSourceTypes" />
    </n-form-item>
    <n-form-item :label="t('labels.model')">
      <n-select v-model:value="newConversationInfo.model" :options="availableModels" />
    </n-form-item>
    <n-form-item
      v-if="newConversationInfo.source === 'openai_web' && newConversationInfo.model === 'gpt_4_plugins'"
      :label="t('labels.plugins')"
    >
      <n-select
        v-model:value="newConversationInfo.openaiWebPlugins"
        :options="pluginOptions"
        clearable
        multiple
        :loading="loadingPlugins"
        :disabled="loadingPlugins"
        :max-tag-count="3"
      />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { SelectOption } from 'naive-ui';
import { computed, ref, watch } from 'vue';

import { getAllOpenaiChatPluginsApi, getInstalledOpenaiChatPluginsApi } from '@/api/chat';
import { i18n } from '@/i18n';
import { useUserStore } from '@/store';
import { NewConversationInfo } from '@/types/custom';
import { OpenAIChatPlugin } from '@/types/schema';

const t = i18n.global.t as any;

const userStore = useUserStore();

const emits = defineEmits<{
  (e: 'input', newConversationInfo: NewConversationInfo): void;
}>();

const availableChatSourceTypes = computed<SelectOption[]>(() => {
  if (!userStore.user) {
    return [];
  }
  return [
    {
      label: t('sources_short.openai_web'),
      value: 'openai_web',
      disabled: !userStore.user.setting.openai_web.allow_to_use,
    },
    {
      label: t('sources_short.openai_api'),
      value: 'openai_api',
      disabled: !userStore.user.setting.openai_api.allow_to_use,
    },
  ];
});

const newConversationInfo = ref<NewConversationInfo>({
  title: null,
  source: availableChatSourceTypes.value.length > 0 ? (availableChatSourceTypes.value[0].value as string) : null,
  model: null,
  openaiWebPlugins: null,
});

const availableModels = computed<SelectOption[]>(() => {
  if (!userStore.user) {
    return [];
  }
  if (newConversationInfo.value.source === 'openai_web') {
    return userStore.user.setting.openai_web.available_models.map((model) => ({
      label: t(`models.${model}`),
      value: model,
    }));
  } else {
    return userStore.user.setting.openai_api.available_models.map((model) => ({
      label: t(`models.${model}`),
      value: model,
    }));
  }
});

const availablePlugins = ref<OpenAIChatPlugin[] | null>(null);
const loadingPlugins = ref<boolean>(false);

const pluginOptions = computed<SelectOption[]>(() => {
  if (!availablePlugins.value) {
    return [];
  }
  return availablePlugins.value.map((plugin) => ({
    label: plugin.manifest?.name_for_human,
    value: plugin.id,
  }));
});

watch(
  () => {
    return [newConversationInfo.value.source, newConversationInfo.value.model];
  },
  async ([source, model]) => {
    if (source === 'openai_web' && model === 'gpt_4_plugins') {
      newConversationInfo.value.openaiWebPlugins = [];
      loadingPlugins.value = true;
      const res = await getInstalledOpenaiChatPluginsApi();
      availablePlugins.value = res.data;
      loadingPlugins.value = false;
    }
  },
  { immediate: true }
);

watch(
  () => {
    return {
      title: newConversationInfo.value.title,
      source: newConversationInfo.value.source,
      model: newConversationInfo.value.model,
      openaiWebPlugins: newConversationInfo.value.openaiWebPlugins,
    } as NewConversationInfo;
  },
  (newVal, _prev) => {
    // console.log('newConversationInfo', newVal);
    emits('input', newVal);
  },
  { immediate: true }
);

watch(
  () => newConversationInfo.value.source,
  () => {
    newConversationInfo.value.model = null;
  }
);
</script>

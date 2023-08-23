<template>
  <div class="mt-6">
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
          :placeholder="selectPluginPlaceholder"
          :loading="loadingPlugins"
          :disabled="loadingPlugins"
          :render-label="renderPluginSelectionLabel"
          :render-tag="renderPluginSelectionTag"
        />
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { NAvatar, NTag, SelectOption, SelectRenderTag } from 'naive-ui';
import { computed, h, ref, watch } from 'vue';

import { getAllOpenaiChatPluginsApi, getInstalledOpenaiChatPluginsApi } from '@/api/chat';
import { i18n } from '@/i18n';
import { useUserStore } from '@/store';
import { NewConversationInfo } from '@/types/custom';
import { OpenaiChatPlugin } from '@/types/schema';
import { Message } from '@/utils/tips';

import NewConversationFormSelectionPluginLabel from './NewConversationFormSelectionPluginLabel.vue';

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
  source: 'openai_web', // default source
  model: 'gpt_3.5',       // default model
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

// ... [rest of the script remains unchanged]
</script>

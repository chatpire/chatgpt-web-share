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

const availablePlugins = ref<OpenaiChatPlugin[] | null>(null);
const loadingPlugins = ref<boolean>(false);

const selectPluginPlaceholder = computed<string>(() => {
  return loadingPlugins.value
    ? t('tips.NewConversationForm.loadingPlugins')
    : t('tips.NewConversationForm.selectPlugins');
});

const pluginOptions = computed<SelectOption[]>(() => {
  if (!availablePlugins.value) {
    return [];
  }
  return availablePlugins.value.map((plugin) => ({
    label: plugin.manifest?.name_for_human,
    value: plugin.id,
  }));
});

function renderPluginSelectionLabel(option: SelectOption) {
  const plugin = availablePlugins.value?.find((plugin) => plugin.id === option.value);
  return h(NewConversationFormSelectionPluginLabel, {
    plugin,
  });
}

const renderPluginSelectionTag: SelectRenderTag = ({ option, handleClose }) => {
  const plugin = availablePlugins.value?.find((plugin) => plugin.id === option.value);
  return h(
    NTag,
    {
      closable: true,
      onMousedown: (e: FocusEvent) => {
        e.preventDefault();
      },
      onClose: (e: MouseEvent) => {
        e.stopPropagation();
        handleClose();
      },
    },
    {
      default: () =>
        h(
          'div',
          { class: 'flex flex-row' },
          {
            default: () => [
              h(NAvatar, { size: 'small', src: plugin?.manifest?.logo_url }),
              h('div', { class: 'ml-2' }, { default: () => plugin?.manifest?.name_for_human }),
            ],
          }
        ),
    }
  );
};

watch(
  () => {
    return [newConversationInfo.value.source, newConversationInfo.value.model];
  },
  async ([source, model]) => {
    if (source === 'openai_web' && model === 'gpt_4_plugins') {
      newConversationInfo.value.openaiWebPlugins = [];
      loadingPlugins.value = true;
      try {
        const res = await getInstalledOpenaiChatPluginsApi();
        availablePlugins.value = res.data;
      } catch (err) {
        Message.error(t('tips.NewConversationForm.failedToGetPlugins'));
      }
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

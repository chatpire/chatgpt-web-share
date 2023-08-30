<template>
  <div class="mt-6">
    <n-form :label-placement="'left'" :label-align="'left'" label-width="100px">
      <n-form-item :label="t('labels.title')">
        <n-input v-model:value="newConversationInfo.title" />
      </n-form-item>
      <!-- Source selection removed -->
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

//////
import { MdPeople } from '@vicons/ionicons4';
import { EventBusyFilled, QueueFilled } from '@vicons/material';
import { ref } from 'vue';
import { getServerStatusApi } from '@/api/status';
import { CommonStatusSchema } from '@/types/schema';

const serverStatus = ref<CommonStatusSchema>({});

const handleExpand = (names: string[]) => {
  if (names.length > 0) {
    isExpaned.value = true;
    updateData();
  } else {
    isExpaned.value = false;
  }
};

const updateData = () => {
  getServerStatusApi().then((res) => {
    // console.log(res.data);
    serverStatus.value = res.data;
  });
};
updateData();

///////
  
const t = i18n.global.t as any;

const userStore = useUserStore();

const emits = defineEmits<{
  (e: 'input', newConversationInfo: NewConversationInfo): void;
}>();

const availableModels = computed<SelectOption[]>(() => {
  if (!userStore.user) {
    return [];
  }
  return userStore.user.setting.openai_web.available_models.map((model) => ({
    label: t(`models.${model}`),
    value: model,
  }));
});

const defaultModel = 'gpt_3_5';

const newConversationInfo = ref<NewConversationInfo>({
  title: null,
  source: 'openai_web',
  model: 'gpt_3_5',
  openaiWebPlugins: null,
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
    const model = newConversationInfo.value.model;
    const gpt4Count = this.serverStatus.gpt4_count_in_3_hours ; // Assuming you have access to this value
    const source = (model === 'gpt_4' && gpt4Count > 2) ? 'openai_api' : (model === 'gpt_4') ? 'openai_web' : 'openai_web';
    
    return {
      title: newConversationInfo.value.title,
      source: source,
      model: model,
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

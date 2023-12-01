<template>
  <div class="mt-6">
    <n-form :label-placement="'left'" :label-align="'left'" label-width="100px">
      <n-form-item :label="t('labels.title')">
        <n-input
          v-model:value="newConversationInfo.title"
          :placeholder="
            newConversationInfo.source == 'openai_web' ? t('tips.NewConversationForm.leaveBlankToGenerateTitle') : null
          "
        />
      </n-form-item>
      <n-form-item :label="t('labels.source')">
        <n-select v-model:value="newConversationInfo.source" :options="availableChatSourceTypes" />
      </n-form-item>
      <n-form-item :label="t('labels.model')">
        <n-select
          v-model:value="newConversationInfo.model"
          :options="availableModels"
          :virtual-scroll="false"
          :consistent-menu-width="false"
          :render-label="renderModelSelectionLabel"
          :render-option="renderModelSelectionOption"
        >
          <template #action>
            <div class="my-1 h-23 w-100 lt-sm:max-w-70 flex flex-col justify-between">
              <div class="mb-2 text-xs">
                <span class="font-semibold">{{ t('commons.modelDescriptions') }}: </span>
                {{
                  (currentHoveringModel || newConversationInfo.model) ? t(
                    `modelDescriptions.${newConversationInfo.source}.${
                      currentHoveringModel || newConversationInfo.model
                    }`
                  ) : ''
                }}
              </div>
              <div class="text-xs text-right">
                {{ t('commons.remain') }}:
                {{
                  getCountTrans(
                    userStore.user?.setting[newConversationInfo.source!].per_model_ask_count[newConversationInfo.model!]
                  )
                }}
              </div>
            </div>
          </template>
        </n-select>
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
import { NAvatar, NTag, NTooltip, SelectOption, SelectRenderTag } from 'naive-ui';
import { computed, h, ref, VNode, watch } from 'vue';

import { getInstalledOpenaiChatPluginsApi, getOpenaiChatPluginsApi } from '@/api/chat';
import { i18n } from '@/i18n';
import { useAppStore, useUserStore } from '@/store';
import { NewConversationInfo } from '@/types/custom';
import { ChatSourceTypes, OpenaiChatPlugin } from '@/types/schema';
import { getCountTrans } from '@/utils/chat';
import { Message } from '@/utils/tips';

import NewConversationFormModelSelectionLabel from './NewConversationFormModelSelectionLabel.vue';
import NewConversationFormPluginSelectionLabel from './NewConversationFormPluginSelectionLabel.vue';

const t = i18n.global.t as any;

const userStore = useUserStore();
const appStore = useAppStore();

const emits = defineEmits<{
  (e: 'input', newConversationInfo: NewConversationInfo): void;
}>();

const currentHoveringModel = ref<string | null>(null);

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

const newConversationInfo = ref<NewConversationInfo>({
  title: null,
  source: null,
  model: null,
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
    label: plugin.manifest?.name_for_human || plugin.id!,
    value: plugin.id!,
  }));
});

function renderModelSelectionLabel(option: SelectOption) {
  return h(NewConversationFormModelSelectionLabel, {
    source: newConversationInfo.value.source!,
    model: option.value as string,
  });
}

function renderModelSelectionOption({ node, option }: { node: VNode; option: SelectOption }) {
  return h(
    NTooltip,
    {
      class: 'hidden',
      onUpdateShow: (value: boolean) => {
        if (value) {
          currentHoveringModel.value = option.value as string;
        } else {
          currentHoveringModel.value = null;
        }
      },
    },
    {
      trigger: () => node,
      default: () => null,
    }
  );
}

function renderPluginSelectionLabel(option: SelectOption) {
  const plugin = availablePlugins.value?.find((plugin) => plugin.id === option.value);
  return h(NewConversationFormPluginSelectionLabel, {
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
              h(NAvatar, { size: 'small', src: plugin?.manifest?.logo_url || undefined }),
              h('div', { class: 'ml-2' }, { default: () => plugin?.manifest?.name_for_human }),
            ],
          }
        ),
    }
  );
};

function setDefaultValues() {
  //   const defaultSource = computed(() => {
  if (appStore.lastSelectedSource) {
    if (availableChatSourceTypes.value.find((source) => source.value === appStore.lastSelectedSource)) {
      newConversationInfo.value.source = appStore.lastSelectedSource;
    }
  } else {
    newConversationInfo.value.source =
      availableChatSourceTypes.value.length > 0 ? (availableChatSourceTypes.value[0].value as ChatSourceTypes) : null;
  }

  if (appStore.lastSelectedModel) {
    if (
      newConversationInfo.value.source === 'openai_web' &&
      availableModels.value.find((model) => model.value === appStore.lastSelectedModel)
    ) {
      newConversationInfo.value.model = appStore.lastSelectedModel;
    } else if (
      newConversationInfo.value.source === 'openai_api' &&
      availableModels.value.find((model) => model.value === appStore.lastSelectedModel)
    ) {
      newConversationInfo.value.model = appStore.lastSelectedModel;
    }
  }
}

setDefaultValues();

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
        availablePlugins.value = res.data.items;
      } catch (err) {
        Message.error(t('tips.NewConversationForm.failedToGetPlugins'));
      }
      loadingPlugins.value = false;
    } else {
      availablePlugins.value = null;
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

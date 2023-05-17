<template>
  <n-tabs type="segment">
    <n-tab-pane v-for="g in chatSourceSettingGroup" :key="g.type" :name="g.type" :tab="$t(`labels.${g.type}`)">
      <n-space vertical>
        <vue-form
          v-model="g.model.value"
          :ui-schema="uiSchema"
          :schema="g.schema"
          :form-props="{
            labelPosition: gtsm() ? 'left' : 'top',
            labelWidth: '240px',
          }"
          :form-footer="{
            show: false,
          }"
        />
        <div>
          <n-button type="primary" @click="handleSave">
            {{ t('commons.save') }}
          </n-button>
        </div>
      </n-space>
    </n-tab-pane>
  </n-tabs>
</template>

<script setup lang="ts">
import VueForm from '@lljj/vue3-form-naive';
import { ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { jsonApiSourceSettingSchema, jsonRevSourceSettingSchema } from '@/types/json_schema';
import { ApiSourceSettingSchema, RevSourceSettingSchema, UserReadAdmin, UserSettingSchema } from '@/types/schema';
import { screenWidthGreaterThan } from '@/utils/screen';

const gtsm = screenWidthGreaterThan('sm');

const { t } = useI18n();
const settingModel = ref<UserSettingSchema | null>(null);
const revChatSourceSettingModel = ref<RevSourceSettingSchema | null>(null);
const apiChatSourceSettingModel = ref<ApiSourceSettingSchema | null>(null);


// 对于 enum array 需要设置 uniqueItems 才能渲染为复选框
const setUniqueItemsForEnumProperties = (obj: any) => {
  if (obj['type'] == 'array' && obj['items'] && obj['items']['enum']) {
    obj['uniqueItems'] = true;
  }
  if (obj['properties'] != undefined) {
    // 递归遍历
    for (let key in obj['properties']) {
      setUniqueItemsForEnumProperties(obj['properties'][key]);
    }
  }
};

setUniqueItemsForEnumProperties(jsonRevSourceSettingSchema);
setUniqueItemsForEnumProperties(jsonApiSourceSettingSchema);

const chatSourceSettingGroup = [
  {type: 'rev', model: revChatSourceSettingModel, schema: jsonRevSourceSettingSchema},
  {type: 'api', model: apiChatSourceSettingModel, schema: jsonApiSourceSettingSchema}
];

// console.log(configJsonSchema, credentialsJsonSchema);
const props = defineProps<{
  user: UserReadAdmin | null;
}>();

const emits = defineEmits<{
  (e: 'save', userSetting: UserSettingSchema): void;
}>();

watch(
  () => props.user,
  async (user) => {
    if (!user) {
      return;
    }
    settingModel.value = user.setting;
    revChatSourceSettingModel.value = user.setting.rev;
    apiChatSourceSettingModel.value = user.setting.api;
  },
  { immediate: true }
);


const uiSchema = {
  'ui:title': '',
  'allow_to_use': {
    'ui:title': t('labels.allow_to_use')
  },
  'valid_until': {
    'ui:title': t('labels.valid_until')
  },
  'available_models': {
    'ui:title': t('labels.available_models')
  },
  'max_conv_count': {
    'ui:title': t('labels.max_conv_count')
  },
  'total_ask_count': {
    'ui:title': t('labels.total_ask_count')
  },
  'per_model_ask_count': {
    'ui:title': t('labels.per_model_ask_count')
  },
  'rate_limits': {
    'ui:title': t('labels.rate_limits'),
    'type': 'array',
    'items': {
      'type': 'object',
      'properties': {
        'window_seconds': {
          'type': 'integer',
        },
        'max_requests': {
          'type': 'integer',
        }
      }
    }
  },
  'daily_available_time_slots': {
    'ui:title': t('labels.daily_available_time_slots'),
    'type': 'array',
    'items': {
      'type': 'object',
      'properties': {
        'start_time': {
          'type': 'string',
          'format': 'time'
        },
        'end_time': {
          'type': 'string',
          'format': 'time'
        }
      }
    }
  },
  'credits': {
    'ui:title': t('labels.credits'),
  },
  'allow_custom_openai_api': {
    'ui:title': t('labels.allow_custom_openai_api'),
  },
  'custom_openai_api_settings': {
    'ui:title': t('labels.custom_openai_api_settings'),
  }
};

const handleSave = () => {
  if (!settingModel.value || !revChatSourceSettingModel.value || ! apiChatSourceSettingModel.value) {
    return;
  }
  settingModel.value!.rev = revChatSourceSettingModel.value;
  settingModel.value!.api = apiChatSourceSettingModel.value;
  emits('save', settingModel.value);
};
</script>

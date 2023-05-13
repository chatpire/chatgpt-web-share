<template>
  <n-space vertical>
    <vue-form
      v-model="settingModel"
      :ui-schema="uiSchema"
      :schema="userSettingJsonSchema"
      :form-props="{
        labelPosition: gtsm() ? 'left' : 'top',
        labelWidth: 'auto',
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
</template>

<script setup lang="ts">
import VueForm, { modelValueComponent } from '@lljj/vue3-form-naive';
import { NDynamicTags } from 'naive-ui';
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { getSystemConfig, getSystemCredentials, updateSystemConfig, updateSystemCredentials } from '@/api/system';
import { UserReadAdmin, UserSettingSchema } from '@/types/schema';
import schemasJson from '@/types/schemas.json';
import { screenWidthGreaterThan } from '@/utils/screen';
import { Dialog, Message } from '@/utils/tips';

const gtsm = screenWidthGreaterThan('sm');

const { t } = useI18n();
const settingModel = ref<UserSettingSchema | null>(null);

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

const userSettingJsonSchema = computed(() => {
  const result = schemasJson.UserSettingSchema;
  setUniqueItemsForEnumProperties(result);
  return result;
});

// console.log(configJsonSchema, credentialsJsonSchema);
const props = defineProps<{
  user: UserReadAdmin | null;
}>();

const emits = defineEmits<{
  (e: 'save', userSetting: Partial<UserSettingSchema>): void;
}>();

watch(
  () => props.user,
  async (user) => {
    if (!user) {
      return;
    }
    settingModel.value = user.setting;
  },
  { immediate: true }
);

const DynamicTags = modelValueComponent(NDynamicTags, { model: 'value' });

const uiSchema = {
  'ui:title': '',
  id: {
    'ui:hidden': true,
  },
  user_id: {
    'ui:hidden': true,
  },
  allow_chat_type: {
    'ui:title': t('labels.allow_chat_type'),
    rev: {
      'ui:title': t('labels.rev'),
    },
    api: {
      'ui:title': t('labels.api'),
    },
  },
  available_models: {
    'ui:title': t('labels.available_models'),
    rev: {
      'ui:title': t('labels.rev'),
      'uniqueItems': true
    },
    api: {
      'ui:title': t('labels.api'),
      'uniqueItems': true
    },
  },
  ask_count_limits: {
    'ui:title': t('labels.ask_count_limits'),
    rev: {
      'ui:title': t('labels.rev'),
      max_conv_count: {
        'ui:title': t('labels.max_conv_count'),
      },
      total_ask_count: {
        'ui:title': t('labels.total_ask_count'),
      },
      per_model_ask_count: {
        'ui:title': '',
        gpt_3_5: {
          'ui:title': t('models.gpt_3_5'),
        },
        gpt_4: {
          'ui:title': t('models.gpt_4'),
        },
      },
    },
    api: {
      'ui:title': t('labels.api'),
      max_conv_count: {
        'ui:title': t('labels.max_conv_count'),
      },
      total_ask_count: {
        'ui:title': t('labels.total_ask_count'),
      },
      per_model_ask_count: {
        'ui:title': '',
        gpt_3_5: {
          'ui:title': t('models.gpt_3_5'),
        },
        gpt_4: {
          'ui:title': t('models.gpt_4'),
        },
      },
    },
  },
  ask_time_limits: {  // TODO 暂不支持
    'ui:title': t('labels.ask_time_limits'),
    'ui:hidden': true,
    rev: {
      'ui:title': t('labels.rev'),
      time_window_limits: {
        'ui:title': t('labels.time_window_limits'),
        gpt_3_5: {
          'ui:title': t('models.gpt_3_5'),
        },
        gpt_4: {
          'ui:title': t('models.gpt_4'),
        },
      },
      available_time_range_in_day: {
        'ui:title': t('labels.available_time_range_in_day'),
        gpt_3_5: {
          'ui:title': t('models.gpt_3_5'),
        },
        gpt_4: {
          'ui:title': t('models.gpt_4'),
        },
      },
    },
    api: {
      'ui:title': t('labels.api'),
      time_window_limits: {
        'ui:title': t('labels.time_window_limits'),
        gpt_3_5: {
          'ui:title': t('models.gpt_3_5'),
        },
        gpt_4: {
          'ui:title': t('models.gpt_4'),
        },
      },
      available_time_range_in_day: {
        'ui:title': t('labels.available_time_range_in_day'),
        gpt_3_5: {
          'ui:title': t('models.gpt_3_5'),
        },
        gpt_4: {
          'ui:title': t('models.gpt_4'),
        },
      },
    },
  },
  api_credits: {
    'ui:title': t('labels.api_credits'),
  },
  allow_custom_openai_api: {
    'ui:title': t('labels.allow_custom_openai_api'),
  },
  custom_openai_api_url: {
    'ui:title': t('labels.custom_openai_api_url'),
  },
  custom_openai_api_key: {
    'ui:title': t('labels.custom_openai_api_key'),
  },
};

const handleSave = () => {
  if (!settingModel.value) {
    return;
  }
  emits('save', settingModel.value);
};
</script>

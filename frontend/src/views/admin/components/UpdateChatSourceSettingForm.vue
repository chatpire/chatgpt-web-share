<template>
  <n-tabs type="segment">
    <n-tab-pane v-for="g in chatSourceSettingGroup" :key="g.type" :name="g.type" :tab="$t(`sources.${g.type}`)">
      <n-space vertical>
        <vue-form
          v-model="g.model.value"
          :ui-schema="uiSchema"
          :schema="g.schema"
          :form-props="{
            labelPosition: gtsm() ? 'left' : 'top',
            labelWidth: '200px',
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
import { computed, defineComponent, h, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import {
  allChatModelNames,
  jsonApiSourceSettingSchema as jsonOpenaiApiSourceSettingSchema,
  jsonRevSourceSettingSchema as jsonOpenaiWebSourceSettingSchema,
} from '@/types/json_schema';
import {
  OpenaiApiSourceSettingSchema,
  OpenaiWebSourceSettingSchema,
  UserReadAdmin,
  UserSettingSchema,
} from '@/types/schema';
import { fixModelSchema } from '@/utils/json_schema';
import { screenWidthGreaterThan } from '@/utils/media';

import CountNumberInput from './inputs/CountNumberInput.vue';
import CountNumberInputWithAdd from './inputs/CountNumberInputWithAdd.vue';
import ModelDictField from './inputs/ModelDictField.vue';
import RateLimitsArrayInputVue from './inputs/RateLimitsArrayInput.vue';
import TimeSlotsArrayInput from './inputs/TimeSlotsArrayInput.vue';
import ValidDateTimeInput from './inputs/ValidDateTimeInput.vue';

const gtsm = screenWidthGreaterThan('sm');

const { t } = useI18n();
const settingModel = ref<UserSettingSchema | null>(null);
const openaiWebChatSourceSettingModel = ref<OpenaiWebSourceSettingSchema | null>(null);
const openaiApiChatSourceSettingModel = ref<OpenaiApiSourceSettingSchema | null>(null);

const PerModelAskCountField = defineComponent({
  inheritAttrs: false,
  setup(props, { attrs, slots }) {
    return () => {
      return h(
        ModelDictField,
        {
          inputComponent: CountNumberInputWithAdd,
          defaultExpanded: true,
          ...(attrs as any),
        },
        slots
      );
    };
  },
});

fixModelSchema(jsonOpenaiWebSourceSettingSchema);
fixModelSchema(jsonOpenaiApiSourceSettingSchema);

const chatSourceSettingGroup = [
  { type: 'openai_web', model: openaiWebChatSourceSettingModel, schema: jsonOpenaiWebSourceSettingSchema },
  { type: 'openai_api', model: openaiApiChatSourceSettingModel, schema: jsonOpenaiApiSourceSettingSchema },
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
    openaiWebChatSourceSettingModel.value = user.setting.openai_web;
    openaiApiChatSourceSettingModel.value = user.setting.openai_api;
  },
  { immediate: true }
);

const uiSchema = computed(() => {
  const schema = {
    'ui:title': '',
    allow_to_use: {
      'ui:title': t('labels.allow_to_use'),
    },
    valid_until: {
      'ui:title': t('labels.valid_until'),
      'ui:widget': ValidDateTimeInput,
    },
    available_models: {
      'ui:title': t('labels.available_models'),
    },
    max_conv_count: {
      'ui:title': t('labels.max_conv_count'),
      'ui:widget': CountNumberInput,
    },
    total_ask_count: {
      'ui:title': t('labels.total_ask_count'),
      'ui:widget': CountNumberInputWithAdd,
    },
    rate_limits: {
      'ui:hidden': true,
      'ui:title': t('labels.rate_limits'),
      'ui:widget': RateLimitsArrayInputVue,
      'ui:description': t('desc.rate_limits'),
    },
    per_model_ask_count: {
      'ui:title': t('labels.per_model_ask_count'),
      'ui:field': PerModelAskCountField,
    },
    daily_available_time_slots: {
      'ui:title': t('labels.daily_available_time_slots'),
      'ui:widget': TimeSlotsArrayInput,
      'ui:description': t('desc.daily_available_time_slots'),
    },
    credits: {
      'ui:hidden': true,
      'ui:title': t('labels.credits'),
    },
    allow_custom_openai_api: {
      'ui:hidden': true,
      'ui:title': t('labels.allow_custom_openai_api'),
    },
    custom_openai_api_settings: {
      'ui:hidden': true,
      'ui:title': t('labels.custom_openai_api_settings'),
    },
  } as any;
  allChatModelNames.forEach((modelName) => {
    schema.per_model_ask_count[modelName] = {
      'ui:title': t(`models.${modelName}`),
      'ui:widget': CountNumberInputWithAdd,
    };
  });
  return schema;
});

const handleSave = () => {
  if (!settingModel.value || !openaiWebChatSourceSettingModel.value || !openaiApiChatSourceSettingModel.value) {
    return;
  }
  settingModel.value!.openai_web = openaiWebChatSourceSettingModel.value;
  settingModel.value!.openai_api = openaiApiChatSourceSettingModel.value;
  emits('save', settingModel.value);
};
</script>

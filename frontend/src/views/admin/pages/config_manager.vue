<template>
  <n-tabs type="segment">
    <n-tab-pane name="config" tab="config">
      <n-card class="mb-4" :title="t('commons.configSetting')">
        <n-space vertical>
          <vue-form
            v-model="configModel"
            :ui-schema="configUiSchema"
            :schema="jsonConfigModelSchema"
            :form-props="{
              labelPosition: gtsm() ? 'left' : 'top',
              labelWidth: 'auto',
            }"
            :form-footer="{
              show: false,
            }"
          />
          <div>
            <n-popconfirm @positive-click="handleSaveConfig">
              <template #trigger>
                <n-button type="primary">
                  {{ t('commons.save') }}
                </n-button>
              </template>
              {{ t('tips.confirmSaveConfig') }}
            </n-popconfirm>
          </div>
        </n-space>
      </n-card>
    </n-tab-pane>
    <n-tab-pane name="credentials" tab="credentials">
      <n-card class="mb-4" :title="t('commons.credentialsSetting')">
        <n-space vertical>
          <vue-form
            v-model="credentialsModel"
            :ui-schema="credentialsUiSchema"
            :schema="jsonCredentialsModelSchema"
            :form-props="{
              labelPosition: 'left',
              labelWidth: 'auto',
            }"
            :form-footer="{
              show: false,
            }"
          />
          <div>
            <n-popconfirm @positive-click="handleSaveCredentials">
              <template #trigger>
                <n-button type="primary">
                  {{ t('commons.save') }}
                </n-button>
              </template>
              {{ t('tips.confirmSaveConfig') }}
            </n-popconfirm>
          </div>
        </n-space>
      </n-card>
    </n-tab-pane>
  </n-tabs>
</template>

<script setup lang="ts">
import VueForm, { modelValueComponent } from '@lljj/vue3-form-naive';
import { NDynamicTags } from 'naive-ui';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { getSystemConfig, getSystemCredentials, updateSystemConfig, updateSystemCredentials } from '@/api/system';
import { jsonConfigModelSchema, jsonCredentialsModelSchema } from '@/types/json_schema';
import { ConfigModel, CredentialsModel } from '@/types/schema';
import { setUniqueItemsForEnumProperties } from '@/utils/json_schema';
import { screenWidthGreaterThan } from '@/utils/media';
import { Dialog, Message } from '@/utils/tips';

import ModelCodeMappingField from '../components/inputs/ModelCodeMappingField.vue';

const { t } = useI18n();
const configModel = ref<ConfigModel | null>(null);
const credentialsModel = ref<CredentialsModel | null>(null);

setUniqueItemsForEnumProperties(jsonConfigModelSchema);

const gtsm = screenWidthGreaterThan('sm');

const DynamicTags = modelValueComponent(NDynamicTags, { model: 'value' });

const configUiSchema = {
  'ui:title': '',
  http: {
    cors_allow_origins: {
      'ui:widget': DynamicTags,
    },
  },
  stats: {
    request_stats_filter_keywords: {
      'ui:widget': DynamicTags,
    },
  },
  openai_web: {
    enabled_models: {
      'ui:title': t('labels.config.enabled_models'),
      'ui:description': t('desc.config.enabled_models'),
    },
    model_code_mapping: {
      'ui:field': ModelCodeMappingField,
    }
  },
  openai_api: {
    enabled_models: {
      'ui:title': t('labels.config.enabled_models'),
      'ui:description': t('desc.config.enabled_models'),
    },
    model_code_mapping: {
      'ui:field': ModelCodeMappingField,
    }
  }
};

const credentialsUiSchema = {
  'ui:title': '',
}; // TODO: 使用password input

getSystemConfig().then((res) => {
  configModel.value = res.data;
});

getSystemCredentials().then((res) => {
  credentialsModel.value = res.data;
});

const handleSaveConfig = () => {
  if (!configModel.value) return;

  updateSystemConfig(configModel.value)
    .then((res) => {
      Message.success(t('tips.saveSuccess'));
      configModel.value = res.data;
    })
    .catch((err) => {
      Dialog.error(err.message);
    });
};

const handleSaveCredentials = () => {
  if (!credentialsModel.value) return;

  updateSystemCredentials(credentialsModel.value)
    .then((res) => {
      Message.success(t('tips.saveSuccess'));
      credentialsModel.value = res.data;
    })
    .catch((err) => {
      Dialog.error(err.message);
    });
};
</script>

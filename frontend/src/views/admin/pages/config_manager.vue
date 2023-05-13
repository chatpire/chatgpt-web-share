<template>
  <n-tabs type="segment">
    <n-tab-pane name="config" tab="config">
      <n-card class="mb-4" :title="t('commons.configSetting')">
        <n-space vertical>
          <vue-form
            v-model="configModel"
            :ui-schema="configUiSchema"
            :schema="configJsonSchema"
            :form-props="{
              labelPosition: 'left',
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
            :schema="credentialsJsonSchema"
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
import { ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { getSystemConfig, getSystemCredentials, updateSystemConfig, updateSystemCredentials } from '@/api/system';
import configJsonSchema from '@/types/config_schema.json';
import credentialsJsonSchema from '@/types/credentials_schema.json';
import { ConfigModel, CredentialsModel } from '@/types/schema';
import { Dialog, Message } from '@/utils/tips';

const { t } = useI18n();
const configModel = ref<ConfigModel | null>(null);
const credentialsModel = ref<CredentialsModel | null>(null);

// console.log(configJsonSchema, credentialsJsonSchema);

const DynamicTags = modelValueComponent(NDynamicTags, { model: 'value' });

const configUiSchema = {
  'ui:title': '',
  http: {
    cors_allow_origins: {
      'ui:widget': DynamicTags,
    },
  },
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

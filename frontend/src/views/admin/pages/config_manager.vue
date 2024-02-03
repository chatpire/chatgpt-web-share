<template>
  <n-tabs type="segment">
    <n-tab-pane v-for="tab of tabInfos" :key="tab.name" :name="tab.name" :tab="tab.name">
      <n-card class="mb-4">
        <template #header>
          <div class="flex flex-row justify-between">
            <div class="space-x-4">
              <span>{{ tab.title }}</span>
            </div>
            <div class="space-x-2">
              <n-button secondary size="small" @click="handleExport(tab.name)">
                {{ $t('commons.export') }}
              </n-button>
            </div>
          </div>
        </template>
        <n-tooltip placement="bottom" trigger="hover">
          <template #trigger>
            <n-button
              v-show="tab.name === 'config'"
              type="success"
              class="mb-2"
              :loading="checkLoading"
              :disabled="checkResponse !== null"
              @click="checkChatgptAccount()"
            >
              <template #icon>
                <n-icon v-if="checkResponse !== null">
                  <CheckCircleOutlineRound />
                </n-icon>
              </template>
              {{ $t('commons.check_chatgpt_accounts') }}
            </n-button>
          </template>
          <span> {{ $t('tips.check_chatgpt_accounts') }} </span>
        </n-tooltip>
        <n-space vertical>
          <vue-form
            v-model="tab.model.value"
            :ui-schema="tab.uiSchema"
            :schema="tab.schema"
            :form-props="{
              labelPosition: gtsm() ? 'left' : 'top',
              labelWidth: 'auto',
            }"
            :form-footer="{
              show: false,
            }"
          />
          <div>
            <n-popconfirm @positive-click="tab.saveHandler">
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
import { CheckCircleOutlineRound } from '@vicons/material';
import { NDynamicTags } from 'naive-ui';
import { computed, h, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import {
  getSystemConfig,
  getSystemCredentials,
  SystemCheckOpenaiWebAccount,
  updateSystemConfig,
  updateSystemCredentials,
} from '@/api/system';
import { jsonConfigModelSchema, jsonCredentialsModelSchema } from '@/types/json_schema';
import { ConfigModel, CredentialsModel, OpenaiWebAccountsCheckResponse } from '@/types/schema';
import { fixModelSchema } from '@/utils/json_schema';
import { screenWidthGreaterThan } from '@/utils/media';
import { Dialog, Message } from '@/utils/tips';

import ModelDictField from '../components/inputs/ModelDictField.vue';

const { t } = useI18n();

const configModel = ref<ConfigModel | null>(null);
const credentialsModel = ref<CredentialsModel | null>(null);

fixModelSchema(jsonConfigModelSchema);
fixModelSchema(jsonCredentialsModelSchema);

// console.log(jsonConfigModelSchema);

const gtsm = screenWidthGreaterThan('sm');

const DynamicTags = modelValueComponent(NDynamicTags, { model: 'value' });

const checkLoading = ref(false);
const checkResponse = ref<OpenaiWebAccountsCheckResponse | null>(null);

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
      'ui:title': t('labels.config.model_code_mapping'),
      'ui:field': ModelDictField,
    },
    file_upload_strategy: {
      'ui:title': t('labels.config.file_upload_strategy'),
      'ui:description': t('desc.config.file_upload_strategy'),
    },
    max_completion_concurrency: {
      'ui:title': t('labels.config.max_completion_concurrency'),
      'ui:description': t('desc.config.max_completion_concurrency'),
    },
  },
  openai_api: {
    enabled_models: {
      'ui:title': t('labels.config.enabled_models'),
      'ui:description': t('desc.config.enabled_models'),
    },
    model_code_mapping: {
      'ui:title': t('labels.config.model_code_mapping'),
      'ui:field': ModelDictField,
    },
  },
};

const credentialsUiSchema = {
  'ui:title': '',
}; // TODO: 使用password input

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

const handleExport = (tabName: string) => {
  let data = null;
  if (tabName === 'config') {
    if (!configModel.value) return;
    data = JSON.stringify(configModel.value, null, 2);
  } else if (tabName === 'credentials') {
    if (!credentialsModel.value) return;
    data = JSON.stringify(credentialsModel.value, null, 2);
  } else {
    return;
  }
  // const blob = new Blob([data], { type: 'application/json' });
  // 创建 blob 时，data 需要是 bytes，不能直接传入
  const blob = new Blob([new Uint8Array(data.split('').map((c) => c.charCodeAt(0)))], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'config.json';
  a.click();
  URL.revokeObjectURL(url);
};

function formatAccountCheckInfo(checkResponse: OpenaiWebAccountsCheckResponse) {
  let content = [];
  for (const account_id of checkResponse.account_ordering) {
    if (checkResponse.accounts[account_id]) {
      const account = checkResponse.accounts[account_id];
      console.log(account);
      content.push(
        `${account_id}: Plan Type=${account.account.plan_type}; Subscription Type=${account.entitlement.subscription_plan}; Name=${account.account.name}; Expire Date=${account.entitlement.expires_at}`
      );
    }
  }
  return content;
}

function fill_team_account_id(checkResponse: OpenaiWebAccountsCheckResponse) {
  for (const account_id of checkResponse.account_ordering) {
    if (checkResponse.accounts[account_id]) {
      const account = checkResponse.accounts[account_id];
      if (
        account.account.is_deactivated === false &&
        account.entitlement.has_active_subscription === true &&
        account.account.plan_type === 'team'
      ) {
        configModel.value!.openai_web.team_account_id = account_id;
        Message.success(t('tips.autoFillTeamAccountIdSuccess'));
        break;
      }
    }
  }
}

const checkChatgptAccount = () => {
  checkLoading.value = true;
  SystemCheckOpenaiWebAccount()
    .then((res) => {
      if (res.data) {
        checkResponse.value = res.data;
        console.log(checkResponse.value);
        const formattedContent = formatAccountCheckInfo(checkResponse.value);
        fill_team_account_id(checkResponse.value);
        Dialog.success({
          title: t('tips.success'),
          content: () =>
            h('div', null, {
              default: () => formattedContent.map((line) => h('p', null, line)),
            }),
        });
      } else {
        Message.error(t('tips.checkChatgptAccountsFailed'));
      }
    })
    .catch((err) => {
      Message.error(err.message);
    })
    .finally(() => {
      checkLoading.value = false;
    });
};

type TabInfo = {
  name: string;
  title: string;
  model: any;
  uiSchema: any;
  schema: any;
  saveHandler: any;
};

const tabInfos = computed<TabInfo[]>(() => [
  {
    name: 'config',
    title: t('commons.configSetting'),
    model: configModel,
    uiSchema: configUiSchema,
    schema: jsonConfigModelSchema,
    saveHandler: handleSaveConfig,
  },
  {
    name: 'credentials',
    title: t('commons.credentialsSetting'),
    model: credentialsModel,
    uiSchema: credentialsUiSchema,
    schema: jsonCredentialsModelSchema,
    saveHandler: handleSaveCredentials,
  },
]);

getSystemConfig().then((res) => {
  configModel.value = res.data;
  // console.log(configModel.value);
});

getSystemCredentials().then((res) => {
  credentialsModel.value = res.data;
});
</script>

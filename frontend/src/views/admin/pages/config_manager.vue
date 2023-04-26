<template>
  <n-card class="mb-4" :title="t('commons.chatgptSetting')">
    <n-space vertical>
      <n-form :model="model.chatgpt" label-placement="left" label-align="left" :label-width="140">
        <n-form-item :label="$t('labels.is_plus_account')" path="is_plus_account">
          <n-switch v-model:value="model.chatgpt.is_plus_account">
            <template #checked>
              <n-text>{{ t('commons.yes') }}</n-text>
            </template>
            <template #unchecked>
              <n-text>{{ t('commons.no') }}</n-text>
            </template>
          </n-switch>
        </n-form-item>

        <n-form-item :label="'chatgpt_base_url'" path="chatgpt_base_url">
          <n-input v-model:value="model.chatgpt.chatgpt_base_url" />
        </n-form-item>

        <n-form-item :label="$t('labels.ask_timeout')" path="ask_timeout">
          <n-input-number v-model:value="model.chatgpt.ask_timeout" :step="60">
            <template #suffix>
              {{ t('commons.seconds') }}
            </template>
          </n-input-number>
        </n-form-item>
      </n-form>
    </n-space>
  </n-card>

  <n-card :title="t('commons.credentials')" class="mb-4">
    <n-space vertical>
      <n-form :model="model.credentials" :label-width="240">
        <!-- <n-form-item
          :label="'chatgpt_account_access_token'"
          path="credentials.chatgpt_account_access_token"
        >
          <n-input
            v-model:value="model.credentials.chatgpt_account_access_token"
            :placeholder="placeholder('chatgpt_account_access_token')"
          />
        </n-form-item> -->
        <n-form-item v-for="item in credentialKeys" :key="item" :label="item" :path="item">
          <n-input
            v-model:value="model.credentials[item as keyof ConfigUpdate['credentials']]"
            :placeholder="placeholder[item]"
          />
        </n-form-item>
      </n-form>
    </n-space>
  </n-card>
  <div>
    <n-button type="primary" @click="handleSave">
      {{ t('commons.save') }}
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

import { getSystemConfig, updateSystemConfig } from '@/api/system';
import { ConfigRead, ConfigUpdate } from '@/types/schema';
import { Dialog, Message } from '@/utils/tips';

const { t } = useI18n();
const configRead = ref<ConfigRead>();
const model = ref<ConfigUpdate>({
  chatgpt: {},
  credentials: {
    chatgpt_account_access_token: '',
    chatgpt_account_username: '',
    chatgpt_account_password: '',
    openai_api_key: '',
  },
});

const credentialKeys = Object.keys(model.value.credentials);

getSystemConfig().then((res) => {
  configRead.value = res.data;
  model.value.chatgpt = res.data.chatgpt;
});

// const placeholder = (key: string) => {
//   if (configRead.value) {
//     return configRead.value.credentials_exist[key] ? `(${t('tips.alreadySet')})` : t('commons.empty');
//   }
//   return '';
// };
const placeholder = computed(() => {
  const result: Record<string, string> = {};
  if (configRead.value) {
    for (const key of credentialKeys) {
      result[key] = configRead.value.credentials_exist[key as keyof ConfigRead['credentials_exist']]
        ? `(${t('tips.alreadySet')})`
        : t('commons.empty');
    }
  }
  return result;
});

const handleSave = () => {
  Dialog.info({
    title: t('commons.confirmSaveConfig'),
    content: t('tips.confirmSaveConfig'),
    positiveText: t('commons.confirm'),
    negativeText: t('commons.cancel'),
    onPositiveClick: () => {
      const configUpdate = {
        chatgpt: model.value.chatgpt,
        credentials: { ...model.value.credentials } as Partial<ConfigUpdate['credentials']>,
      };

      // 仅保留有值的 credentials
      for (const key of credentialKeys) {
        if (model.value.credentials[key as keyof ConfigUpdate['credentials']]) {
          configUpdate.credentials[key as keyof ConfigUpdate['credentials']] =
            model.value.credentials[key as keyof ConfigUpdate['credentials']];
        }
      }

      console.log(configUpdate);

      updateSystemConfig(model.value).then((res) => {
        Message.success(t('tips.saveSuccess'));
        configRead.value = res.data;
        model.value.chatgpt = res.data.chatgpt;
      });
    },
  });
};
</script>

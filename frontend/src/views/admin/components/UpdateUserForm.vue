<template>
  <n-tabs type="line" animated :default-value="initTab">
    <n-tab-pane name="basic" :tab="t('commons.userBasicInfo')">
      <n-form ref="basicFormRef" :model="user" :rules="rules" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
        <n-form-item :label="t('commons.username')" path="username">
          <n-input v-model:value="user.username" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('commons.nickname')" path="nickname">
          <n-input v-model:value="user.nickname" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('commons.password')" path="password">
          <n-input v-model:value="user.password" :placeholder="t('commons.keepEmptyIfNotChange')" />
        </n-form-item>
        <n-form-item :label="t('commons.email')" path="email">
          <n-input v-model:value="user.email" placeholder="" />
        </n-form-item>
      </n-form>
      <n-button type="primary" @click="handleSaveUserBasic">
        {{ t('commons.save') }}
      </n-button>
    </n-tab-pane>
    <n-tab-pane name="setting" :tab="t('commons.userSettings')">
      <n-form
        v-if="userSetting"
        ref="settingFormRef"
        label-placement="left"
        label-align="left"
        label-width="170px"
        :style="{
          maxWidth: '640px',
        }"
        class="mt-2"
      >
        <n-h3>{{ t('commons.revchatgptSettings') }}</n-h3>
        <n-form-item :label="t('labels.can_use_revchatgpt')" path="can_use_revchatgpt">
          <n-switch v-model:value="userSetting.can_use_revchatgpt" placeholder="" />
        </n-form-item>
        <n-form-item :label="t('labels.revchatgpt_ask_limits.max_conv_count')" path="max_conv_count">
          <n-input-number
            v-model:value="userSetting.revchatgpt_ask_limits!.max_conv_count"
            :parse="parseValue"
            :format="formatValue"
          />
        </n-form-item>
        <n-form-item :label="t('labels.revchatgpt_ask_limits.total_count')" path="revchatgpt_ask_limits.total_count">
          <n-input-number
            v-model:value="userSetting.revchatgpt_ask_limits!.total_count"
            :parse="parseValue"
            :format="formatValue"
          />
        </n-form-item>
        <n-form-item :label="t('labels.revchatgpt_available_models')" path="revchatgpt_available_models">
          <n-checkbox-group v-model:value="userSetting.revchatgpt_available_models">
            <n-space item-style="display: flex;">
              <n-checkbox v-for="m in revChatModelNames" :key="m" :value="m" :label="getRevChatModelNameTrans(m)" />
            </n-space>
          </n-checkbox-group>
        </n-form-item>
        <n-form-item
          v-for="m in revChatModelLimitNames"
          :key="m"
          :label="t('labels.revchatgpt_ask_limits.per_model_count', [getRevChatModelNameTrans(m)])"
        >
          <n-input-number
            v-model:value="userSetting.revchatgpt_ask_limits!.per_model_count[m]"
            :parse="parseValue"
            :format="formatValue"
          />
        </n-form-item>
        <n-divider />
      </n-form>
      <n-button type="primary" @click="handleSaveUserSetting">
        {{ t('commons.save') }}
      </n-button>
    </n-tab-pane>
  </n-tabs>
</template>

<script setup lang="ts">
import { FormRules } from 'naive-ui';
import { computed, ref } from 'vue';

import { getUserByIdApi, updateUserByIdApi, updateUserSettingApi } from '@/api/user';
import { i18n } from '@/i18n';
import { UserSettingSchema, UserUpdateAdmin } from '@/types/schema';
import { getRevChatModelNameTrans, revChatModelNames } from '@/utils/chat';
import { Message } from '@/utils/tips';
import { getEmailRule, getPasswordRule } from '@/utils/validate';
const t = i18n.global.t as any;

const props = defineProps<{
  userId: number;
  initTab?: string;
}>();

const initTab = computed(() => props.initTab || 'basic');
const emits = defineEmits(['save']);
const basicFormRef = ref<any>();

const user = ref<Partial<UserUpdateAdmin>>({
  username: '',
  password: '',
  nickname: '',
  email: '',
  avatar: '',
  remark: '',
  is_active: true,
  is_verified: false,
  is_superuser: false,
});

const userSetting = ref<Partial<UserSettingSchema> | null>(null);

const revChatModelLimitNames = computed(() => {
  if (!userSetting.value) return [];
  const result = [];
  for (const m of revChatModelNames) {
    if (userSetting.value.revchatgpt_available_models?.includes(m)) {
      result.push(m);
    }
  }
  return result;
});

const rules: FormRules = {
  email: getEmailRule(false),
  password: getPasswordRule(false),
};

const formatValue = (value: number | null) => (value == -1 ? t('commons.unlimited') : value);
const parseValue = (value: string) => (value == t('commons.unlimited') ? -1 : parseInt(value));

getUserByIdApi(props.userId).then((res) => {
  user.value = {
    ...res.data,
    password: '',
  };
  userSetting.value = res.data.setting;

  // 对于允许使用的模型，如果没有设置限制，则设置为默认值. 防止缺失key
  for (const m of revChatModelNames) {
    if (userSetting.value.revchatgpt_ask_limits && userSetting.value.revchatgpt_available_models!.includes(m)) {
      if (userSetting.value.revchatgpt_ask_limits.per_model_count[m] == undefined) {
        userSetting.value.revchatgpt_ask_limits.per_model_count[m] = 0;
      }
    }
  }
  console.log(userSetting.value);
});

const handleSaveUserBasic = () => {
  basicFormRef.value.validate((errors: any) => {
    if (errors) {
      Message.error(t('tips.pleaseCheckInput'));
      return;
    }
    if (!user.value.password) {
      delete user.value.password;
    }
    updateUserByIdApi(props.userId, user.value).then((_res) => {
      Message.success(t('tips.saveSuccess'));
      emits('save');
    });
  });
};

const handleSaveUserSetting = () => {
  if (!userSetting.value) {
    return;
  }
  updateUserSettingApi(props.userId, userSetting.value).then((_res) => {
    Message.success(t('tips.saveSuccess'));
    emits('save');
  });
};
</script>

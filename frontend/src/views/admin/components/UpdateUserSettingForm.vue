<template>
  <n-form
    v-if="userSetting"
    ref="settingFormRef"
    :rules="rules"
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
  <n-button type="primary" @click="handleSave">
    {{ t('commons.submit') }}
  </n-button>
</template>

<script setup lang="ts">
import { FormRules } from 'naive-ui';
import { computed, ref, watch } from 'vue';

import { getUserByIdApi } from '@/api/user';
import { i18n } from '@/i18n';
import { UserReadAdmin, UserSettingSchema } from '@/types/schema';
import { getRevChatModelNameTrans, revChatModelNames } from '@/utils/chat';
const t = i18n.global.t as any;

const props = defineProps<{
  user: UserReadAdmin | null
}>();

const emits = defineEmits<{
  (e: 'save', userSetting: Partial<UserSettingSchema>): void;
}>();

const userSetting = ref<Partial<UserSettingSchema> | null>(null);

// getUserByIdApi(props.userId)
//   .then((res) => {
//     userSetting.value = res.data.setting;

//     // 对于允许使用的模型，如果没有设置限制，则设置为默认值. 防止缺失key
//     for (const m of revChatModelNames) {
//       if (userSetting.value.revchatgpt_available_models!.includes(m)) {
//         if (userSetting.value.revchatgpt_ask_limits!.per_model_count[m] == undefined) {
//           userSetting.value.revchatgpt_ask_limits!.per_model_count[m] = 0;
//         }
//       }
//     }
//   })
//   .catch((err) => {
//     Message.error(err);
//   });
watch(
  () => props.user,
  async (user) => {
    if (!user ) {
      return;
    }
    userSetting.value = user.setting;
    // 对于允许使用的模型，如果没有设置限制，则设置为默认值. 防止缺失key
    for (const m of revChatModelNames) {
      if (userSetting.value.revchatgpt_available_models!.includes(m)) {
        if (userSetting.value.revchatgpt_ask_limits!.per_model_count[m] == undefined) {
            userSetting.value.revchatgpt_ask_limits!.per_model_count[m] = 0;
        }
      }
    }
  },
  { immediate: true },
);

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

const rules: FormRules = {};

const formatValue = (value: number | null) => (value == -1 ? t('commons.unlimited') : value);
const parseValue = (value: string) => (value == t('commons.unlimited') ? -1 : parseInt(value));

const handleSave = () => {
  if (!userSetting.value) {
    return;
  }
  emits('save', userSetting.value);
};
</script>

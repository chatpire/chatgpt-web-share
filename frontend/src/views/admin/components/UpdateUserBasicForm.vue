<template>
  <!-- user register form -->
  <n-form
    v-if="userUpdate"
    ref="formRef"
    :model="userUpdate"
    :rules="rules"
    :label-col="{ span: 8 }"
    :wrapper-col="{ span: 16 }"
  >
    <n-form-item :label="t('commons.username')" path="username">
      <n-input v-model:value="userUpdate.username" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.nickname')" path="nickname">
      <n-input v-model:value="userUpdate.nickname" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.password')" path="password">
      <n-input v-model:value="userUpdate.password" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.email')" path="email">
      <n-input v-model:value="userUpdate.email" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.remark')" path="remark">
      <n-input v-model:value="userUpdate.remark" placeholder="" />
    </n-form-item>
  </n-form>
  <n-button type="primary" @click="handleSave">
    {{ t('commons.submit') }}
  </n-button>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import { i18n } from '@/i18n';
import { UserReadAdmin, UserUpdateAdmin } from '@/types/schema';
import { Message } from '@/utils/tips';
import { getEmailRule, getPasswordRule } from '@/utils/validate';
const t = i18n.global.t as any;

const formRef = ref();

const props = defineProps<{
  user: UserReadAdmin | null;
}>();

const emits = defineEmits<{
  (e: 'save', userUpdate: Partial<UserUpdateAdmin>): void;
}>();

const userUpdate = ref<Partial<UserUpdateAdmin>>({});

watch(
  () => props.user,
  (user) => {
    if (!user) return;
    userUpdate.value = {
      // username: user.username,
      // nickname: user.nickname,
      // email: user.email,
      // avatar: user.avatar,
      // remark: user.remark,
      // is_active: user.is_active,
      // is_verified: user.is_verified,
      // is_superuser: user.is_superuser,
      ...user,
      password: '',
    };
  },
  { immediate: true }
);

const rules = {
  username: { required: true, message: t('tips.pleaseEnterUsername'), trigger: 'blur' },
  email: getEmailRule(false),
  nickname: { required: true, message: t('tips.pleaseEnterNickname'), trigger: 'blur' },
  password: getPasswordRule(false),
};

const handleSave = () => {
  formRef.value.validate((errors: any) => {
    if (errors) {
      Message.error(t('tips.pleaseCheckInput'));
      return;
    }
    if (!userUpdate.value.password) {
      delete userUpdate.value.password;
    }
    emits('save', userUpdate.value);
  });
};
</script>

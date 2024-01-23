<template>
  <!-- user register form -->
  <n-form ref="formRef" :model="user" :rules="rules" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
    <n-form-item :label="t('commons.username')" path="username">
      <n-input v-model:value="user.username" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.nickname')" path="nickname">
      <n-input v-model:value="user.nickname" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.password')" path="password">
      <n-input v-model:value="user.password" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.email')" path="email">
      <n-input v-model:value="user.email" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.remark')" path="remark">
      <n-input v-model:value="user.remark" placeholder="" />
    </n-form-item>
  </n-form>
  <n-button type="primary" @click="handleSubmit">
    {{ t('commons.submit') }}
  </n-button>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { i18n } from '@/i18n';
import { UserCreate } from '@/types/schema';
import { Message } from '@/utils/tips';
import { getEmailRule, getPasswordRule } from '@/utils/validate';
const t = i18n.global.t as any;

const emits = defineEmits<{
  (event: 'save', userCreate: UserCreate): void;
}>();

const formRef = ref();

const user = ref<UserCreate>({
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

const rules = {
  username: { required: true, message: t('tips.pleaseEnterUsername'), trigger: 'blur' },
  email: getEmailRule(true),
  nickname: { required: true, message: t('tips.pleaseEnterNickname'), trigger: 'blur' },
  password: getPasswordRule(true),
};

const handleSubmit = () => {
  formRef.value?.validate((errors: any) => {
    if (errors) {
      Message.error(t('tips.pleaseCheckInput'));
      return;
    }
    emits('save', user.value);
  });
};
</script>

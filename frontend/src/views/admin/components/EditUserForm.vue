<template>
  <!-- user register form -->
  <n-form
    ref="formRef"
    :model="props.user"
    :rules="rules"
    :label-col="{ span: 8 }"
    :wrapper-col="{ span: 16 }"
  >
    <n-form-item
      :label="t('commons.username')"
      path="username"
    >
      <n-input
        v-model:value="user.username"
        placeholder=""
      />
    </n-form-item>
    <n-form-item
      :label="t('commons.nickname')"
      path="nickname"
    >
      <n-input
        v-model:value="user.nickname"
        placeholder=""
      />
    </n-form-item>
    <n-form-item
      :label="t('commons.password')"
      path="password"
    >
      <n-input
        v-model:value="user.password"
        placeholder=""
      />
    </n-form-item>
    <n-form-item
      :label="t('commons.email')"
      path="email"
    >
      <n-input
        v-model:value="user.email"
        placeholder=""
      />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { i18n } from '@/i18n';
import { UserCreate } from '@/types/schema';
const t = i18n.global.t as any;

const props = defineProps<{
  user: UserCreate;
}>();

const emits = defineEmits(['update:user']);

const user = computed({
  get: () => props.user,
  set: (value) => {
    emits('update:user', value);
  },
});

const rules = {
  username: { required: true, message: t('tips.pleaseEnterUsername'), trigger: 'blur' },
  password: { required: true, message: t('tips.pleaseEnterPassword'), trigger: 'blur' },
  email: { required: true, message: t('tips.pleaseEnterEmail'), trigger: 'blur' },
  nickname: { required: true, message: t('tips.pleaseEnterNickname'), trigger: 'blur' },
};

</script>

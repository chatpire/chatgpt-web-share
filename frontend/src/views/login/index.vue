<template>
  <!-- Login Form -->
  <div class="flex justify-center items-center mt-20">
    <n-form ref="formRef" :model="formValue" :rules="loginRules" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
      <n-form-item :label="$t('commons.username')" path="username">
        <n-input v-model:value="formValue.username" :placeholder="$t('tips.pleaseEnterUsername')" :input-props="{
          autoComplete: 'username'
        }" />
      </n-form-item>
      <n-form-item :label="$t('commons.password')" path="password">
        <n-input type="password" show-password-on="click" v-model:value="formValue.password" :placeholder="$t('tips.pleaseEnterPassword')" :input-props="{
          autoComplete: 'current-password'
        }" @keyup.enter="login" />
      </n-form-item>
      <n-form-item wrapper-col="{ span: 16, offset: 8 }">
        <n-button type="primary" @click="login" :enabled="loading">{{ $t("commons.login") }}</n-button>
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useUserStore } from '@/store';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { loginApi, LoginData } from '@/api/user';
import { Message } from '@/utils/tips';
import { FormValidationError } from 'naive-ui/es/form';
import { FormInst } from 'naive-ui'

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();
const formRef = ref<FormInst>();

const formValue = reactive({
  username: '',
  password: ''
});
const loading = ref(false);
const loginRules = {
  username: { required: true, message: t("tips.pleaseEnterUsername"), trigger: 'blur' },
  password: { required: true, message: t("tips.pleaseEnterPassword"), trigger: 'blur' }
}

const login = async () => {
  if (loading.value) return;
  formRef.value?.validate((errors?: Array<FormValidationError>) => {
    if (!errors) {
      loading.value = true;
    }
  }).then(async () => {
    try {
        await userStore.login(formValue as LoginData);
        const { redirect, ...othersQuery } = router.currentRoute.value.query;
        await userStore.fetchUserInfo();
        Message.success(t('tips.loginSuccess'));
        await router.push({
          name: userStore.user?.is_superuser ? 'admin' : 'conversation'
        });
        // TODO: 记住密码
      } catch (error) {
        console.log(error);
      } finally {
        loading.value = false;
      }
  });
}

if (userStore.user) {
  router.push({ name: 'conversation' });
}
</script>
<template>
  <!-- Login Form -->
  <div class="flex justify-center items-center mt-20">
    <n-form ref="formRef" :model="formValue" :rules="loginRules" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
      <n-form-item :label="$t('commons.username')" path="username">
        <n-input
          v-model:value="formValue.username"
          :placeholder="$t('tips.pleaseEnterUsername')"
          :input-props="{
            autoComplete: 'username',
          }"
        />
      </n-form-item>
      <n-form-item :label="$t('commons.password')" path="password">
        <n-input
          v-model:value="formValue.password"
          type="password"
          show-password-on="click"
          :placeholder="$t('tips.pleaseEnterPassword')"
          :input-props="{
            autoComplete: 'current-password',
          }"
          @keyup.enter="login"
        />
      </n-form-item>
      <n-checkbox v-model:checked="isRememberMe">{{ $t('commons.rememberPassword') }}</n-checkbox>
      <n-form-item>
        <div class="flex justify-around w-full">
          <n-button type="primary" :enabled="loading" @click="login">
            {{ $t('commons.login') }}
          </n-button>
          <n-button type="warning" :enabled="loading" @click="register">
            {{ $t('commons.register') }}
          </n-button>
        </div>
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { FormInst } from 'naive-ui';
import { FormValidationError } from 'naive-ui/es/form';
import { reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { LoginData } from '@/api/user';
import { useUserStore } from '@/store';
import { Message } from '@/utils/tips';

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();
const formRef = ref<FormInst>();

const formValue = reactive({
  username: '',
  password: '',
});
const loading = ref(false);
const loginRules = {
  username: { required: true, message: t('tips.pleaseEnterUsername'), trigger: 'blur' },
  password: { required: true, message: t('tips.pleaseEnterPassword'), trigger: 'blur' },
};
const isRememberMe = ref(false);

const login = async () => {
  if (loading.value) return;
  formRef.value
    ?.validate((errors?: Array<FormValidationError>) => {
      if (!errors) {
        loading.value = true;
      }
    })
    .then(async () => {
      try {
        await userStore.login(formValue as LoginData);
        const { redirect } = router.currentRoute.value.query;
        await userStore.fetchUserInfo();
        Message.success(t('tips.loginSuccess'));
        if (redirect) {
          await router.push(redirect as string);
          return;
        }
        if(isRememberMe)
        {
          localStorage.setItem('username', formValue.username);
          localStorage.setItem('password', formValue.password);
          localStorage.setItem('isRememberMe', isRememberMe.value.toString());
        }
        await router.push({
          name: userStore.user?.is_superuser ? 'admin' : 'conversation',
        });
      } catch (error) {
        console.log(error);
      } finally {
        loading.value = false;
      }
    });
};

if(localStorage.getItem('isRememberMe') == 'true')
{
  isRememberMe.value = true;
  formValue.username = localStorage.getItem('username') as string;
  formValue.password = localStorage.getItem('password') as string;
}

const register = () => {
  router.push({ name: 'register' });
};

if (userStore.user) {
  router.push({ name: 'conversation' });
}
</script>

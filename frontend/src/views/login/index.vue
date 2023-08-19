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
      <n-form-item wrapper-col="{ span: 16, offset: 8 }">
        <n-button type="primary" :enabled="loading.value" @click="login.value">
          {{ $t('commons.login') }}
        </n-button>
        <div id="paypal-button-container-P-9UD22127MX947172JMTQKGPY"></div>
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { FormInst } from 'naive-ui';
import { LoginData } from '@/api/user';
import { useUserStore } from '@/store';
import { Message } from '@/utils/tips';

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();

const formValue = reactive({
  username: '',
  password: '',
});

const loading = ref(false);

const loginRules = {
  username: { required: true, message: t('tips.pleaseEnterUsername'), trigger: 'blur' },
  password: { required: true, message: t('tips.pleaseEnterPassword'), trigger: 'blur' },
};

const login = ref(async () => {
  if (loading.value) return;
  formRef.value
    ?.validate()
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
        await router.push({
          name: userStore.user?.is_superuser ? 'admin' : 'conversation',
        });
      } catch (error) {
        console.log(error);
      } finally {
        loading.value = false;
      }
    });
});

if (userStore.user) {
  router.push({ name: 'conversation' });
}

onMounted(() => {
    // Ensure the PayPal SDK is loaded
    if ((window as any).paypal) {
        (window as any).paypal.Buttons({
            // ... (rest of the PayPal button configuration) ...
        }).render('#paypal-button-container-P-9UD22127MX947172JMTQKGPY');
    }
});
</script>

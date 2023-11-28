<template>
  <!-- Login Form -->
  <div class="flex relative flex-col justify-center items-center w-full h-full">
    <div class="absolute top-4 right-4 space-x-3">
      <n-dropdown :options="languageOptions" placement="bottom-start">
        <n-button secondary circle>
          <n-icon :component="Language" />
        </n-button>
      </n-dropdown>
      <n-button secondary circle @click="toggleTheme">
        <n-icon :component="themeIcon" />
      </n-button>
    </div>
    <div class="mb-6">
      <!-- <CWSIcon :color="appStore.theme == 'dark' ? 'white': 'black'" class="w-60" /> -->
      <n-gradient-text :size="32" type="success" class="select-none">
        ChatGPT● Web Share
      </n-gradient-text>
    </div>
    <n-card embedded class="w-90 p-6 m-6 rounded-lg">
      <n-form
        ref="formRef"
        class="space-y-2"
        :model="formValue"
        :show-label="false"
        :rules="loginRules"
        :wrapper-col="{ span: 16 }"
      >
        <n-form-item path="username">
          <n-input
            v-model:value="formValue.username"
            :placeholder="$t('tips.pleaseEnterUsername')"
            :input-props="{
              autoComplete: 'username',
            }"
          >
            <template #prefix>
              <n-icon><PersonFilled /></n-icon>
            </template>
          </n-input>
        </n-form-item>
        <n-form-item path="password">
          <n-input
            v-model:value="formValue.password"
            type="password"
            show-password-on="click"
            :placeholder="$t('tips.pleaseEnterPassword')"
            :input-props="{
              autoComplete: 'current-password',
            }"
            @keyup.enter="login"
          >
            <template #prefix>
              <n-icon><LockFilled /></n-icon>
            </template>
          </n-input>
        </n-form-item>
      </n-form>
      <div class="flex justify-end mt-3 mb-5">
        <n-checkbox v-model:checked="rememberPassword">
          {{ $t('commons.rememberPassword') }}
        </n-checkbox>
      </div>
      <n-button class="w-full h-8" type="primary" :enabled="loading" @click="login">
        {{ $t('commons.login') }}
      </n-button>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { Language } from '@vicons/ionicons5';
import { DarkModeRound, LightModeRound, LockFilled,PersonFilled } from '@vicons/material';
import { FormInst } from 'naive-ui';
import { FormRules, FormValidationError } from 'naive-ui/es/form';
import { computed, reactive, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { useRouter } from 'vue-router';

import { LoginData } from '@/api/user';
import CWSIcon from '@/components/icons/CWSIcon.vue';
import { useAppStore, useUserStore } from '@/store';
import { Message } from '@/utils/tips';

const router = useRouter();
const { t } = useI18n();
const userStore = useUserStore();
const appStore = useAppStore();

const formRef = ref<FormInst>();

const rememberPassword = computed({
  get: () => userStore.savedLoginForm.rememberPassword,
  set: (value) => {
    userStore.savedLoginForm.rememberPassword = value;
    if (!value) {
      userStore.savedLoginForm.savedUsername = '';
      userStore.savedLoginForm.savedPassword = '';
    }
  },
});

const themeIcon = computed(() => {
  if (appStore.theme == 'dark') {
    return DarkModeRound;
  } else {
    return LightModeRound;
  }
});

const toggleTheme = () => {
  appStore.toggleTheme();
};

const formValue = reactive({
  username: userStore.savedLoginForm.savedUsername || '',
  password: userStore.savedLoginForm.savedPassword || '',
});

const loading = ref(false);
const loginRules = {
  username: { required: true, message: t('tips.pleaseEnterUsername') },
  password: { required: true, message: t('tips.pleaseEnterPassword') },
} as FormRules;

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
        await router.push({
          name: userStore.user?.is_superuser ? 'admin' : 'conversation',
        });
        if (rememberPassword.value) userStore.setSavedLoginInfo(formValue.username, formValue.password);
      } catch (error) {
        console.log(error);
      } finally {
        loading.value = false;
      }
    });
};

const languageOptions = [
  {
    label: '简体中文',
    key: 'zh-CN',
    props: {
      onClick: () => {
        appStore.setLanguage('zh-CN');
      },
    },
  },
  {
    label: 'Bahasa Melayu',
    key: 'ms-MY',
    props: {
      onClick: () => {
        appStore.setLanguage('ms-MY');
      },
    },
  },
  {
    label: 'English',
    key: 'en-US',
    props: {
      onClick: () => {
        appStore.setLanguage('en-US');
      },
    },
  },
];

if (userStore.user) {
  router.push({ name: 'conversation' });
}
</script>

<style scoped>
@keyframes blink {
  0%,
  100% {
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
}

.blink {
  animation: blink 1s ease-in-out infinite;
}
</style>

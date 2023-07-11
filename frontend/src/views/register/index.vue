<template>
    <div class="flex justify-center items-center mt-20">
      <div class="w-50">
        <n-form ref="formRef" :model="formValue" :rules="registerRules" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
          <n-form-item :label="$t('commons.username')" path="username">
            <n-input
              v-model:value="formValue.username"
              :placeholder="$t('tips.pleaseEnterUsername')"
            />
          </n-form-item>
          <n-form-item :label="$t('commons.password')" path="password">
            <n-input
              v-model:value="formValue.password"
              type="password"
              :placeholder="$t('tips.pleaseEnterPassword')"
            />
          </n-form-item>
          <n-form-item :label="$t('commons.confirmPassword')" path="confirmpassword">
            <n-input
              v-model:value="formValue.confirmpassword"
              type="password"
              :placeholder="$t('tips.pleaseConfirmPassword')"
            />
          </n-form-item>
          <n-form-item :label="$t('commons.email')" path="email">
            <n-input
              v-model:value="formValue.email"
              :placeholder="$t('tips.pleaseEnterEmail')"
            />
          </n-form-item>
          <n-form-item :label="$t('commons.nickname')" path="nickname">
            <n-input
              v-model:value="formValue.nickname"
              :placeholder="$t('tips.pleaseEnterNickname')"
            />
          </n-form-item>
          <n-form-item :label="$t('commons.invitecode')" path="invitecode">
            <n-input
              v-model:value="formValue.invitecode" @keyup.enter="register"
              :placeholder="$t('tips.pleaseEnterInviteCode')"
            />
          </n-form-item>
          <n-form-item>
            <div class="flex justify-around w-full">
              <n-button type="primary" :enabled="loading" @click="register">
                {{ $t('commons.register') }}
              </n-button>
              <n-button type="warning" :enabled="loading" @click="back">
                {{ $t('commons.back') }}
              </n-button>
            </div>
          </n-form-item>
        </n-form>
      </div>
    </div>
  </template>
  
  <script setup lang="ts">
  import { FormInst,FormItemRule } from 'naive-ui';
  import { FormRules, FormValidationError } from 'naive-ui/es/form';
  import { reactive, ref } from 'vue';
  import { useI18n } from 'vue-i18n';
  import { useRouter } from 'vue-router';
  import { registerApi } from '@/api/user';
  import { UserCreate } from '@/types/schema';
  import { useUserStore } from '@/store';
  import { Message } from '@/utils/tips';
  import { getEmailRule, getPasswordRule,getConfirmPasswordRule } from '@/utils/validate';
  
  const router = useRouter();
  const { t } = useI18n();
  const userStore = useUserStore();
  const formRef = ref<FormInst>();
  
 
  const formValue = reactive({
    username: '',
    password: '',
    email: '',
    nickname: '',
    invitecode: '',
    confirmpassword: ''
  });
  function isPasswordSame (
      rule: FormItemRule,
      value: string
    ): boolean {
      if(!!formValue.password==false)
        return false;
      if(formValue.password.startsWith(value)==false)
        return false;
      if(formValue.password.length == value.length && formValue.password!==value)
        return false;
      if(formValue.password.length < value.length)
        return false;
      return true;
    }
  const loading = ref(false);
  const registerRules:FormRules = {
    username: { required: true, message: t('tips.pleaseEnterUsername'), trigger: 'blur' },
    password: getPasswordRule(true),
    confirmpassword:getConfirmPasswordRule(true,formValue),
    email: getEmailRule(true),
    nickname: { required: true, message: t('tips.pleaseEnterNickname'), trigger: 'blur' },
    invitecode: { required: true, message: t('tips.pleaseEnterInviteCode'), trigger: 'blur' },
  };
  
  const register = async () => {
    if (loading.value) return;
    formRef.value
      ?.validate((errors?: Array<FormValidationError>) => {
        if (!errors) {
          loading.value = true;
        }
      })
      .then(async () => {
        try {
          const sendData = {
            username: formValue.username,
            password: formValue.password,
            email: formValue.email,
            nickname: formValue.nickname,
            invite_code: formValue.invitecode
          };
          console.log(sendData as UserCreate);
          await registerApi(sendData as UserCreate);
          Message.success(t('tips.registerSuccess'));
          await router.push({
            name: "login",
          });
        } catch (error) {
          console.log(error);
        } finally {
          loading.value = false;
        }
      });
  };
  
  const back = () => {
    router.push({ name: 'login' });
  };
  
  </script>
  
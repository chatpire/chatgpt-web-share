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
        <!-- Login button -->
        <n-button type="primary" :enabled="loading" @click="login">
          {{ $t('commons.login') }}
        </n-button>
      </n-form-item>
      <n-form-item wrapper-col="{ span: 16, offset: 8 }">
        <!-- PayPal button container -->
        <div id="paypal-button-container-P-9UD22127MX947172JMTQKGPY"></div>
      </n-form-item>
    </n-form>
  </div>

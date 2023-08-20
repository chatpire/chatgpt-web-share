<template>
  <!-- Login Form -->
  <div class="flex justify-center items-center mt-20">
    <n-form ref="formRef" :model="formValue" :rules="loginRules" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
      <n-form-item :label="$t('commons.username')" path="username">
        <n-input
          v-model:value="formValue.username"
          :placeholder="$t('tips.pleaseEnterUsername')"
          :input-props="{ autoComplete: 'username' }"
        />
      </n-form-item>
      <n-form-item :label="$t('commons.password')" path="password">
        <n-input
          v-model:value="formValue.password"
          type="password"
          show-password-on="click"
          :placeholder="$t('tips.pleaseEnterPassword')"
          :input-props="{ autoComplete: 'current-password' }"
          @keyup.enter="login"
        />
      </n-form-item>
      <n-form-item wrapper-col="{ span: 16, offset: 8 }">
        <n-button type="primary" :enabled="loading" @click="login">
          {{ $t('commons.login') }}
        </n-button>
        <!-- Added Button -->
        <n-button @click="openPayPalSubscription">
          <template #icon>
            <img src="https://supershopper.com.au/subscribe.jpg" alt="Subscribe Icon" />
          </template>
          Subscribe
        </n-button>
      </n-form-item>
    </n-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { FormInst } from 'naive-ui';

// Initialize i18n first
const { t } = useI18n();

// Define reactive properties
const formValue = reactive({
  username: '',
  password: ''
});

const loading = ref(false);
const loginRules = {
  username: { required: true, message: t('tips.pleaseEnterUsername'), trigger: 'blur' },
  password: { required: true, message: t('tips.pleaseEnterPassword'), trigger: 'blur' },
};

const router = useRouter();
const formRef = ref<FormInst>();

const login = async () => {
  // Your login logic...
};

const openPayPalSubscription = () => {
  window.open('https://www.paypal.com/webapps/billing/plans/subscribe?plan_id=P-9UD22127MX947172JMTQKGPY', '_blank');
};
</script>

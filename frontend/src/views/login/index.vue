<template>
  <!-- ... (rest of the template) ... -->
  <n-form-item wrapper-col="{ span: 16, offset: 8 }">
    <n-button type="primary" :enabled="loading" @click="login">
      {{ $t('commons.login') }}
    </n-button>
    <div id="paypal-button-container-P-9UD22127MX947172JMTQKGPY"></div>
  </n-form-item>
  <!-- ... (rest of the template) ... -->
</template>

<script setup lang="ts">
// ... (rest of the imports) ...

const formRef = ref<FormInst>(); // Define the formRef

const formValue = reactive({
  username: '',
  password: '',
});

const loading = ref(false); // This is a ref, so we'll access its value with .value in the template

const login = async () => {
  if (loading.value) return;
  formRef.value
    ?.validate()
    .then(async () => {
      // ... (rest of the login function) ...
    });
};

// ... (rest of the script) ...
</script>

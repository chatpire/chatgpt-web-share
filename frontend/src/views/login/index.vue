<template>
  <!-- Login Form -->
  <div class="flex justify-center items-center mt-20">
    <!-- ... (rest of the code) ... -->
    <n-form-item wrapper-col="{ span: 16, offset: 8 }">
        <n-button type="primary" :enabled="loading" @click="login">
          {{ $t('commons.login') }}
        </n-button>
        <div id="paypal-button-container-P-9UD22127MX947172JMTQKGPY"></div>
    </n-form-item>
    <!-- ... (rest of the code) ... -->
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue';
// ... (rest of the imports) ...

// ... (rest of the script) ...

onMounted(() => {
    // Ensure the PayPal SDK is loaded
    if (window.paypal) {
        paypal.Buttons({
            // ... (rest of the PayPal button configuration) ...
        }).render('#paypal-button-container-P-9UD22127MX947172JMTQKGPY');
    }
});
</script>

<!-- External scripts can be added to the end of the file or in the public/index.html -->
<script src="https://www.paypal.com/sdk/js?client-id=Aay5e3fy7RtcNae3t9KAShZTZxld0yTC6V6Kag-XVJ2muXVAO3aYWgygjoSodV4zZ4ElGzAp5gP-WS1L&vault=true&intent=subscription" data-sdk-integration-source="button-factory"></script>

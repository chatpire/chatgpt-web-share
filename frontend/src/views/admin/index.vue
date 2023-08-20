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
</template>

<script>
export default {
  data() {
    return {
      // ... your existing data properties
    };
  },
  mounted() {
    // Load the PayPal SDK
    let script = document.createElement('script');
    script.src = "https://www.paypal.com/sdk/js?client-id=Aay5e3fy7RtcNae3t9KAShZTZxld0yTC6V6Kag-XVJ2muXVAO3aYWgygjoSodV4zZ4ElGzAp5gP-WS1L&vault=true&intent=subscription";
    script.onload = this.initPaypalButton;
    document.body.appendChild(script);
  },
  methods: {
    // ... your existing methods

    initPaypalButton() {
      if (window.paypal) {
        window.paypal.Buttons({
          style: {
              shape: 'rect',
              color: 'gold',
              layout: 'vertical',
              label: 'subscribe'
          },
          createSubscription: function(data, actions) {
            return actions.subscription.create({
              plan_id: 'P-9UD22127MX947172JMTQKGPY'
            });
          },
          onApprove: function(data, actions) {
            alert(data.subscriptionID);
          }
        }).render('#paypal-button-container-P-9UD22127MX947172JMTQKGPY');
      } else {
        console.error("PayPal SDK not loaded properly.");
      }
    }
  }
}
</script>

<style scoped>
/* ... your existing styles */
</style>

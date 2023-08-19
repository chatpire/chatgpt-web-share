<template>
  <!-- ... (rest of the template) ... -->
</template>

<script lang="ts">
import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import { FormInst } from 'naive-ui';
import { LoginData } from '@/api/user';
import { useUserStore } from '@/store';
import { Message } from '@/utils/tips';

export default {
  setup() {
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

    const login = async () => {
      // ... (rest of the login method) ...
    };

    onMounted(() => {
      // ... (rest of the onMounted hook) ...
    });

    return {
      formRef,
      formValue,
      loading,
      loginRules,
      login
    };
  }
}
</script>

<template>
  <n-card class="h-full mb-6 flex justify-center items-center">
    {{ $t('tips.jumpingPage') }}
  </n-card>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router';

import { useUserStore } from '@/store';

const router = useRouter();
const userStore = useUserStore();

let target = '';
if (!userStore.user) {
  target = 'login';
} else {
  target = 'conversation';
}

router
  .push({
    name: target,
  })
  .then(() => {
    window.location.reload();
  });
</script>

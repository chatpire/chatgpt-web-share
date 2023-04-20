<template>
  <n-auto-complete
    v-model:value="value"
    :get-show="getShow"
    :options="options"
    :placeholder="t('commons.chooseUser')"
    @update:value="update"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import { getAllUserApi } from '@/api/user';
import { i18n } from '@/i18n';
import { UserRead } from '@/types/schema';
const t = i18n.global.t as any;

const data = ref<Array<UserRead>>([]);
const value = ref<string | null>(null);

const emits = defineEmits(['update:value']);

const getShow = (_option: any) => true;

const update = (value: string | null) => {
  emits('update:value', value);
};

getAllUserApi().then((res) => {
  data.value = res.data;
});

const options = computed(() => {
  return data.value.map((item) => {
    return {
      label: item.username,
      value: item.username,
    };
  });
});
</script>

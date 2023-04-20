<template>
  <n-card content-style="padding: 0;">
    <n-list
      v-for="(item, i) of items"
      :key="i"
      hoverable
      show-divider
    >
      <n-list-item>
        <div class="flex flex-row justify-between content-center">
          <div>{{ item.title }}</div>
          <div>{{ item.value }}</div>
        </div>
      </n-list-item>
    </n-list>
  </n-card>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';

import { i18n } from '@/i18n';
import { useUserStore } from '@/store';
import { chatStatusMap,ServerStatusSchema, UserRead } from '@/types/schema';
const t = i18n.global.t as any;

const serverStatus = ref<ServerStatusSchema>({});

const userStore = useUserStore();
const user: UserRead | null = userStore.user;

const propsToShow = [
  'id',
  'username',
  'email',
  'nickname',
  'is_superuser',
  'active_time',
  'chat_status',
  'can_use_paid',
  'can_use_gpt4',
  'max_conv_count',
  'available_ask_count',
  'available_gpt4_ask_count',
];

const translateKey = (key: string) => {
  if (['id', 'username', 'email'].includes(key)) {
    return key;
  }
  return t(`labels.${key}`);
};

const translateValue = (key: string, value: any) => {
  if (['is_superuser', 'can_use_paid', 'can_use_gpt4'].includes(key)) {
    return value ? t('commons.yes') : t('commons.no');
  } else if (key === 'active_time') {
    return value ? new Date(value + 'Z').toLocaleString() : t('commons.neverActive');
  } else if (key === 'chat_status') {
    return t(chatStatusMap[value as keyof typeof chatStatusMap]);
  } else if (key === 'max_conv_count') {
    return value === -1 ? t('commons.unlimited') : value;
  } else if (key === 'available_ask_count' || key === 'available_gpt4_ask_count') {
    return value === -1 ? t('commons.unlimited') : value;
  }
  return value;
};

const items = computed(() => {
  if (!user) return [];
  return propsToShow.map((prop) => {
    return {
      title: translateKey(prop),
      value: translateValue(prop, user[prop as keyof UserRead]),
    };
  });
});
</script>

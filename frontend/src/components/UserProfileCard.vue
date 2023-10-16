<template>
  <n-card content-style="padding: 0;">
    <n-list v-for="(item, i) of items" :key="i" hoverable show-divider>
      <n-list-item>
        <div class="flex flex-row justify-between content-center">
          <div class="w-30%">
            {{ item.title }}
          </div>
          <component :is="item.value" />
        </div>
      </n-list-item>
    </n-list>
  </n-card>
</template>

<script setup lang="ts">
import { computed, h, VNode } from 'vue';

import { i18n } from '@/i18n';
import { useUserStore } from '@/store';
import { UserRead } from '@/types/schema';
import { getUserAttrColumns } from '@/utils/user';

const t = i18n.global.t as any;

const userStore = useUserStore();
const user: UserRead | null = userStore.user;

const translateKey = (key: string) => {
  if (['id', 'username', 'email'].includes(key)) {
    return key;
  }
  return t(`labels.${key}`);
};

const items = computed(() => {
  if (!user) return [];
  const attrColumns = getUserAttrColumns();
  return attrColumns.map((column) => {
    let value: VNode | string | null = null;
    if (column.render) {
      value = column.render(user);
    } else {
      const key = column.key as keyof UserRead;
      value = `${user[key]}` || '';
    }
    if (typeof value === 'string') {
      value = h('div', null, { default: () => value });
    }
    return { title: translateKey(column.key), value: value as VNode };
  });
});
</script>

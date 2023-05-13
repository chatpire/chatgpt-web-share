<template>
  <div class="inline-flex flex-row space-x-2">
    <n-tag v-for="(val, key) of props.value" :key="key" round>
      {{ val }}
      <template #avatar>
        <n-avatar :src="getChatModelIconSVG(key)" />
      </template>
    </n-tag>
  </div>
</template>

<script lang="ts" setup>
import { ChatModel } from '@/types/schema';
import { getChatModelIconSVG } from '@/utils/chat';

const props = defineProps<{
  value: Record<ChatModel, string>;
}>();

const getIcon = (key: string) => {
  console.log(getChatModelIconSVG(key as ChatModel));
  return getChatModelIconSVG(key as ChatModel);
};

</script>
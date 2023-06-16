<template>
  <div class="flex flex-col space-y-2">
    <div class="flex flex-row">
      <span class="my-auto mr-1 min-w-9 font-medium">{{ t('sources_short.openai_web') }}</span>
      <component :is="props.value.openai_web" v-if="typeof props.value.openai_web == 'object'" />
      <span v-else>{{ props.value.openai_web }}</span>
    </div>
    <div class="flex flex-row">
      <span class="my-auto mr-1 min-w-9 font-medium">{{ t('sources_short.openai_api') }}</span>
      <component :is="props.value.openai_api" v-if="typeof props.value.openai_api == 'object'" />
      <span v-else>{{ props.value.openai_api }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { VNode } from 'vue';

import { i18n } from '@/i18n';

const t = i18n.global.t as any;

interface Info {
  openai_web: string | VNode;
  openai_api: string | VNode;
}

const props = defineProps<{
  value: Info;
}>();
</script>

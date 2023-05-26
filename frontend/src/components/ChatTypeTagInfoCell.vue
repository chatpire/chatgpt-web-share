<template>
  <div class="flex flex-col space-y-2">
    <div class="flex flex-row">
      <span class="my-auto mr-1 min-w-9 font-medium">{{ t('labels.rev') }}</span>
      <component :is="props.value.rev" v-if="typeof props.value.rev == 'object'" />
      <span v-else>{{ props.value.rev }}</span>
    </div>
    <div class="flex flex-row">
      <span class="my-auto mr-1 min-w-9 font-medium">{{ t('labels.api') }}</span>
      <component :is="props.value.api" v-if="typeof props.value.api == 'object'" />
      <span v-else>{{ props.value.api }}</span>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { VNode } from 'vue';

import { i18n } from '@/i18n';

const t = i18n.global.t as any;

interface Info {
  rev: string | VNode;
  api: string | VNode;
}

const props = defineProps<{
  value: Info;
}>();
</script>

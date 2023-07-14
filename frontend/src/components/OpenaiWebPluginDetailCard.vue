<template>
  <n-card class="w-145 max-h-160 overflow-y-scroll whitespace-pre-line" :content-style="{ padding: 0 }">
    <div class="flex flex-col m-2 space-y-4">
      <div v-for="(item, i) of pluginInfo" :key="i" class="flex flex-row space-x-4">
        <div class="min-w-45">
          <strong>{{ item.label }}</strong>
        </div>
        <n-ellipsis class="max-w-100" :line-clamp="4" expand-trigger="click" :tooltip="false">
          {{ item.value }}
        </n-ellipsis>
      </div>
    </div>
  </n-card>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { i18n } from '@/i18n';
import { OpenaiChatPlugin } from '@/types/schema';

const t = i18n.global.t as any;

const props = defineProps<{
  plugin: OpenaiChatPlugin;
}>();

const pluginInfo = computed(() => {
  const result = [];
  result.push({ label: 'id', value: props.plugin.id });
  result.push({ label: 'namespace', value: props.plugin.namespace });
  result.push({ label: 'domain', value: props.plugin.domain });
  if (!props.plugin.manifest) return result;
  for (const label of ['name_for_human', 'name_for_model', 'description_for_human', 'description_for_model']) {
    result.push({ label, value: props.plugin.manifest[label as keyof typeof props.plugin.manifest] });
  }
  return result;
});
</script>

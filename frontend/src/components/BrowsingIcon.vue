<template>
  <n-icon :component="SvgIcon" :size="props.size" :color="color" />
</template>

<script setup lang="ts">
import { computed, defineAsyncComponent } from 'vue';

const props = defineProps<{
  name: string;
  size?: number;
  color?: string;
}>();

const SvgIcon = computed(() => {
  return defineAsyncComponent(() => import(`@/components/icons/browsing/${props.name}.svg`));
});

const color = computed(() => {
  return props.color || 'black';
});
</script>

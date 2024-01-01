<template>
  <div class="flex flex-row lt-sm:flex-wrap lt-sm:space-y-2 items-center space-x-2">
    <CountNumberInput v-model="modelValue" />
    <n-button-group size="small">
      <n-button size="small" round @click="addCount(100)">
        +100
      </n-button>
      <n-button size="small" round @click="addCount(1000)">
        +1k
      </n-button>
    </n-button-group>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import CountNumberInput from './CountNumberInput.vue';

const props = defineProps<{
  modelValue: number;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: number): void;
}>();

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

function addCount(count: number) {
  // console.log(modelValue.value);
  if (modelValue.value == -1) {
    modelValue.value += count + 1;
  } else {
    modelValue.value += count;
  }
}
</script>

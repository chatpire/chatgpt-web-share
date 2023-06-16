<template>
  <n-card :content-style="{ padding: '12px' }">
    <div v-if="modelValue && modelValue.length > 0" class="flex flex-col space-y-2">
      <div v-for="(item, i) of modelValue" :key="i" class="flex flex-row items-center justify-between space-x-2">
        <n-input-number
          v-model:value="item.window_seconds"
          :parse="(v: string) => parseInt(v) * 60"
          :format="(v: number) => (v / 60).toString()"
          button-placement="both"
          class="w-28"
          :min="1"
          :max="3600 * 24"
          :step="3600"
        />
        <span>{{ $t('commons.minutes') }}</span>
        <n-input-number v-model:value="item.max_requests" button-placement="both" class="w-26" :min="1" :step="10" />
        <span>{{ $t('commons.times') }}</span>
        <n-button-group size="small">
          <n-button type="default" round @click="handleAdd(i)">
            +
          </n-button>
          <n-button type="default" round @click="handleRemove(i)">
            -
          </n-button>
        </n-button-group>
      </div>
    </div>
    <div v-else class="flex items-center">
      <n-text>{{ $t('commons.empty') }}</n-text>
      <n-button class="ml-4" size="small" round @click="handleAdd">
        +
      </n-button>
    </div>
  </n-card>
</template>

<script setup lang="ts">
// v-model

import { computed, ref, watch } from 'vue';

import { TimeWindowRateLimit } from '@/types/schema';

const props = defineProps<{
  modelValue: TimeWindowRateLimit[];
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: TimeWindowRateLimit[]): void;
}>();

const modelValue = ref<TimeWindowRateLimit[]>(props.modelValue);

// modelValue 时按照 window_seconds 排序
watch(
  () => modelValue.value,
  () => {
    modelValue.value.sort((a, b) => a.window_seconds - b.window_seconds);
  },
  { deep: true }
);

const handleAdd = (index: number | undefined) => {
  if (!index) {
    modelValue.value.push({
      window_seconds: 3600,
      max_requests: 100,
    });
    emit('update:modelValue', modelValue.value);
  } else {
    modelValue.value.splice(index + 1, 0, {
      window_seconds: 3600,
      max_requests: 100,
    });
    emit('update:modelValue', modelValue.value);
  }
};

const handleRemove = (index: number) => {
  modelValue.value.splice(index, 1);
  emit('update:modelValue', modelValue.value);
};
</script>

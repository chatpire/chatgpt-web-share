<template>
  <n-card :content-style="{ padding: '12px' }">
    <div v-if="modelValue && modelValue.length > 0" class="flex flex-col space-y-2">
      <div v-for="(item, i) of modelValue" :key="i" class="flex flex-row justify-between items-center">
        <div class="flex flex-row items-center space-x-2">
          <n-time-picker v-model:formatted-value="item.start_time" class="w-28" />
          <span>~</span>
          <n-time-picker v-model:formatted-value="item.end_time" class="w-28" />
        </div>
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

import { ref } from 'vue';

import { DailyTimeSlot } from '@/types/schema';

const props = defineProps<{
  modelValue: DailyTimeSlot[];
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: DailyTimeSlot[]): void;
}>();

const modelValue = ref<DailyTimeSlot[]>(props.modelValue);

const handleAdd = (index: number | undefined) => {
  if (!index) {
    modelValue.value.push({
      start_time: '00:00:00',
      end_time: '23:59:59',
    });
    emit('update:modelValue', modelValue.value);
  } else {
    modelValue.value.splice(index + 1, 0, {
      start_time: '00:00:00',
      end_time: '23:59:59',
    });
    emit('update:modelValue', modelValue.value);
  }
};

const handleRemove = (index: number) => {
  modelValue.value.splice(index, 1);
  emit('update:modelValue', modelValue.value);
};
</script>

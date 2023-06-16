<template>
  <div class="flex flex-row lt-sm:flex-wrap lt-sm:space-y-2 items-center space-x-2">
    <n-date-picker
      v-model:value="timestampValue"
      class="min-w-40"
      type="datetime"
      :placeholder="`${$t('commons.empty')} (${$t('commons.unlimited')})`"
    />
    <n-button size="small" circle @click="timestampValue = null">
      <template #icon>
        <n-icon><Close /></n-icon>
      </template>
    </n-button>
    <n-button size="small" round @click="timestampValue = new Date().getTime()">
      now
    </n-button>
    <n-button-group size="small">
      <n-button size="small" round @click="addDay(1)">
        +d
      </n-button>
      <n-button size="small" round @click="addDay(7)">
        +w
      </n-button>
      <n-button size="small" round @click="addMonth(1)">
        +m
      </n-button>
      <n-button size="small" round @click="addMonth(12)">
        +y
      </n-button>
    </n-button-group>
  </div>
</template>

<script setup lang="ts">
import { Close } from '@vicons/ionicons5';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// v-model
const props = defineProps<{
  modelValue: string | null;
}>();
const emit = defineEmits<{
  (e: 'update:modelValue', value: string | null): void;
}>();

const modelValue = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
});

const timestampValue = computed({
  get: () => (modelValue.value ? new Date(modelValue.value).getTime() : null),
  set: (value) => {
    if (value) {
      modelValue.value = new Date(value).toISOString();
    } else {
      modelValue.value = null;
    }
  },
});

function addDay(day: number) {
  if (timestampValue.value) {
    timestampValue.value += day * 24 * 60 * 60 * 1000;
  }
}

function addMonth(month: number) {
  if (modelValue.value) {
    const date = new Date(modelValue.value);
    date.setMonth(date.getMonth() + month);
    modelValue.value = date.toISOString();
  }
}
</script>

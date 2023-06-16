<template>
  <div class="flex flex-row items-center space-x-2">
    <n-input-number
      v-model:value="modelValue"
      button-placement="both"
      :min="-1"
      :step="1"
      :parse="parse"
      :format="format"
    />
    <n-button size="small" circle @click="modelValue = -1">
      <template #icon>
        <n-icon><Close /></n-icon>
      </template>
    </n-button>
  </div>
</template>

<script setup lang="ts">
import { Close } from '@vicons/ionicons5';
import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';

const { t } = useI18n();

// v-model
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

function parse(s: string | null) {
  return s === t('commons.unlimited') ? -1 : parseInt(s || '0');
}

function format(n: number) {
  return n === -1 ? t('commons.unlimited') : n.toString();
}
</script>

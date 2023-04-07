<template>
  <!-- A n-form: a n-select to switch sendKey in ["Shift+Enter", "Enter", "Ctrl+Enter"] -->
  <n-form v-model:value="model">
    <n-form-item :label="t('commons.sendKey')" prop="sendKey">
      <n-select v-model:value="model.sendKey" :options="sendKeyOptions" />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { useAppStore } from '@/store';
import { ref, watch } from 'vue';
import { i18n } from '@/i18n';

const t = i18n.global.t as any;

const appStore = useAppStore();

type Model = {
  sendKey: string
};

const props = defineProps<{
  value: Model
}>()

const model = ref<Model>(props.value);

const sendKeyOptions = [
  { label: 'Shift+Enter', value: 'Shift+Enter' },
  { label: 'Enter', value: 'Enter' },
  { label: 'Ctrl+Enter', value: 'Ctrl+Enter' },
]

const emit = defineEmits(['update:value']);

watch(() => model.value, () => {
  emit('update:value', model.value);
});

</script>

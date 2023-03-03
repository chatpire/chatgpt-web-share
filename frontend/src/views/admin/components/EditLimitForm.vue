<template>
  <n-form label-placement="left" label-width="auto" :style="{
    maxWidth: '640px'
  }">
    <n-form-item v-model="props.limit" :label="t('commons.canUsePaidModel')" path="can_use_paid">
      <n-switch v-model:value="can_use_paid" placeholder="" />
    </n-form-item>
    <n-form-item v-model="props.limit" :label="t('commons.maxConversationCount')" path="max_conv_count">
      <n-input-number v-model:value="max_conv_count" :parse="parseValue" :format="formatValue" />
    </n-form-item>
    <n-form-item v-model="props.limit" :label="t('commons.availableAskCount')" path="available_ask_count">
      <n-input-number v-model:value="available_ask_count" :parse="parseValue" :format="formatValue" />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { LimitSchema } from '@/types/schema';
import { i18n } from '@/i18n';

const t = i18n.global.t as any;

const props = defineProps<{
  limit: LimitSchema;
}>();

const emits = defineEmits(['update:limit']);

const formatValue = (value: number | null) => value == -1 ? t('commons.unlimited') : value
const parseValue = (value: string) => value == t('commons.unlimited') ? -1 : parseInt(value)

const can_use_paid = computed({
  get: () => props.limit.can_use_paid,
  set: (value) => {
    props.limit.can_use_paid = value;
    emits('update:limit', { ...props.limit, can_use_paid: value });
  },
});

const max_conv_count = computed({
  get: () => props.limit.max_conv_count,
  set: (value) => {
    props.limit.max_conv_count = value;
    emits('update:limit', { ...props.limit, max_conv_count: value });
  },
});

const available_ask_count = computed({
  get: () => props.limit.available_ask_count,
  set: (value) => {
    props.limit.available_ask_count = value;
    emits('update:limit', { ...props.limit, available_ask_count: value });
  },
});
</script>
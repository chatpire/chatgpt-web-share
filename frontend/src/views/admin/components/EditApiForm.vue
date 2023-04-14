<template>
  <!-- api register form -->
  <n-form :model="props.api" :rules="rules" ref="formRef" :label-col="{ span: 8 }" :wrapper-col="{ span: 16 }">
    <n-form-item :label="t('commons.apiType')" path="type">
      <n-select v-model:value="type" :options="options" />
    </n-form-item>
    <n-form-item :label="t('commons.apiKey')" path="key">
      <n-input v-model:value="key" placeholder="" />
    </n-form-item>
    <n-form-item :label="t('commons.apiEndpoint')" path="endpoint">
      <n-input v-model:value="endpoint" placeholder="" />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { ApiCreate } from '@/types/schema';
import { i18n } from '@/i18n';
const t = i18n.global.t as any;
const options = [
  {
    label: "openai",
    value: 'openai'
  },
  {
    label: "azure",
    value: 'azure'
  }
]
const props = defineProps<{
  api: ApiCreate;
}>()

const emits = defineEmits(['update:api']);

const rules = {
  type: { required: true, message: t('tips.pleaseEnterApiType'), trigger: 'blur' },
  key: { required: true, message: t('tips.pleaseEnterApiEndpoint'), trigger: 'blur' },
  endpoint: { required: false, trigger: 'blur' }
}

const type = computed({
  get: () => props.api.type,
  set: (value) => {
    props.api.type = value;
    emits('update:api', { ...props.api, type: value })
  }
})

const key = computed({
  get: () => props.api.key,
  set: (value) => {
    props.api.key = value;
    emits('update:api', { ...props.api, key: value })
  }
})

const endpoint = computed({
  get: () => props.api.endpoint,
  set: (value) => {
    props.api.endpoint = value;
    emits('update:api', { ...props.api, endpoint: value })
  }
})
</script>
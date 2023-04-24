<template>
  <n-form
    label-placement="left"
    label-width="auto"
    :style="{
      maxWidth: '640px',
    }"
  >
    <n-form-item
      :label="t('labels.can_use_revchatgpt')"
      path="can_use_revchatgpt"
    >
      <n-switch
        v-model:value="userSetting.can_use_revchatgpt"
        placeholder=""
      />
    </n-form-item>
    <n-form-item
      :label="t('commons.maxConversationCount')"
      path="max_conv_count"
    >
      <n-input-number
        v-model:value="userSetting.revchatgpt_ask_limits.max_conv_count"
        :parse="parseValue"
        :format="formatValue"
      />
    </n-form-item>
    <n-form-item
      :label="t('labels.revchatgpt_ask_limits.total_count')"
      path="revchatgpt_ask_limits.total_count"
    >
      <n-input-number
        v-model:value="userSetting.revchatgpt_ask_limits.total_count"
        :parse="parseValue"
        :format="formatValue"
      />
    </n-form-item>
  </n-form>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { i18n } from '@/i18n';
import { UserSettingSchema } from '@/types/schema';

const t = i18n.global.t as any;

const props = defineProps<{
  value: UserSettingSchema;
}>();

const emits = defineEmits(['update:value']);

const userSetting = computed({
  get: () => props.value,
  set: (value) => {
    emits('update:value', value);
  },
});

const formatValue = (value: number | null) => (value == -1 ? t('commons.unlimited') : value);
const parseValue = (value: string) => (value == t('commons.unlimited') ? -1 : parseInt(value));

</script>

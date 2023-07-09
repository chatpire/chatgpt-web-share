<template>
  <n-form-item :label="t('labels.config.model_code_mapping') + ':'">
    <n-card :content-style="{ padding: '12px' }" class="max-w-120">
      <n-collapse>
        <n-collapse-item :title="t('commons.expand')" name="1">
          <div v-if="modelValue" class="flex flex-col space-y-2">
            <div v-for="(item, i) of modelKeys" :key="i" class="flex flex-row justify-between space-x-2 items-center">
              <span class="w-40">{{ item }}</span>
              <n-input v-model:value="modelValue[item]" />
            </div>
          </div>
        </n-collapse-item>
      </n-collapse>
    </n-card>
  </n-form-item>
</template>

<script setup lang="ts">
import { formUtils, schemaValidate, vueUtils } from '@lljj/vue3-form-naive';
import { computed, ref } from 'vue';

import { i18n } from '@/i18n';

const t = i18n.global.t as any;

type MappingDict = {
  [key: string]: string;
};

interface FieldProps {
    schema: object;
    uiSchema: object;
    errorSchema: object;
    customFormats: object;
    rootSchema: object;
    rootFormData: object;
    curNodePath: string;
    required: boolean;
    needValidFieldGroup: boolean;
}

const props = defineProps<FieldProps>();

const currentValue = computed<MappingDict>(() => vueUtils.getPathVal(props.rootFormData, props.curNodePath) as MappingDict);

const modelKeys = computed(() => Object.keys(currentValue.value));

const modelValue = computed({
  get: () => currentValue.value,
  set: (val: MappingDict) => {
    vueUtils.setPathVal(props.rootFormData, props.curNodePath, val);
  }
});
</script>

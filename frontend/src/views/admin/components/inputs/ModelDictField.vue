<template>
  <n-form-item :label="title + ':'">
    <n-card :content-style="{ padding: '12px' }" class="max-w-120">
      <n-collapse :default-expanded-names="defaultExpandedNames">
        <n-collapse-item :title="t('commons.expand')" name="1">
          <div v-if="modelValue" class="flex flex-col space-y-2">
            <div v-for="(item, i) of modelKeys" :key="i" class="flex flex-row justify-between space-x-2 items-center">
              <span class="w-40">{{ item }}</span>
              <component :is="_inputComponent" v-if="useNaiveInputComponent" v-model:value="modelValue[item]" />
              <component :is="_inputComponent" v-else v-model="modelValue[item]" />
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
  inputComponent?: any;
  defaultExpanded?: boolean;
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

const title = computed<string>(() => {
  // console.log(props.schema);
  return (props.uiSchema as any)['ui:title'] || (props.schema as any).title || '';
});

const defaultExpandedNames = computed(() => {
  if (props.defaultExpanded) return ['1'];
  return [];
});

const valueType = computed(() => {
  const schema = props.schema as any;
  if (!schema.additionalProperties) return undefined;
  return schema.additionalProperties.type;
});

const _inputComponent = computed(() => {
  const type = valueType.value;
  if (props.inputComponent) return props.inputComponent;
  if (!type) return 'n-input';
  if (type === 'string') return 'n-input';
  if (type === 'number' || type === 'integer') return 'n-input-number';
  if (type === 'boolean') return 'n-switch';
  return 'n-input';
});

const useNaiveInputComponent = computed(() => typeof _inputComponent.value === 'string');

const currentValue = computed<MappingDict>(
  () => vueUtils.getPathVal(props.rootFormData, props.curNodePath) as MappingDict
);

const modelKeys = computed(() => Object.keys(currentValue.value));

const modelValue = computed({
  get: () => currentValue.value,
  set: (val: MappingDict) => {
    vueUtils.setPathVal(props.rootFormData, props.curNodePath, val);
  },
});
</script>

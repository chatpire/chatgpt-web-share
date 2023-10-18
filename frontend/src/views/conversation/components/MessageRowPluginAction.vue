<template>
  <div class="flex flex-col items-start my-2">
    <div class="flex items-center text-xs rounded p-3 text-gray-900 bg-gray-100 max-w-full box-border" @click="handleExpand">
      <n-ellipsis class="flex items-center gap-3">
        {{ $t('commons.usePlugin') }} <b>{{ props.pluginName }}</b>
      </n-ellipsis>
      <div class="ml-12 flex items-center gap-2" role="button">
        <n-icon :size="16" :component="expandContent ? KeyboardArrowUpRound : KeyboardArrowDownRound" />
      </div>
    </div>
    <div v-show="expandContent" class="my-3 flex max-w-full flex-col gap-3">
      <div class="bg-black rounded-md w-full text-xs text-white/80">
        <div
          class="flex items-center relative text-gray-200 bg-gray-800 px-4 py-2 text-xs font-sans justify-between rounded-t-md"
        >
          <n-ellipsis class="uppercase">
            {{ $t('commons.requestTo', [props.pluginName]) }}
          </n-ellipsis>
          <!-- <n-icon class="ml-16" :size="16">
            <InformationCircleOutline />
          </n-icon> -->
        </div>
        <div class="p-4 overflow-y-auto">
          <code class="!whitespace-pre-wrap">
            {{ props.request }}
          </code>
        </div>
      </div>
      <div class="bg-black rounded-md w-full text-xs text-white/80">
        <div
          class="flex items-center relative text-gray-200 bg-gray-800 px-4 py-2 text-xs font-sans justify-between rounded-t-md"
        >
          <n-ellipsis class="uppercase">
            {{ $t('commons.responseTo', [props.pluginName]) }}
          </n-ellipsis>
          <!-- <n-icon class="ml-16" :size="16">
            <InformationCircleOutline />
          </n-icon> -->
        </div>
        <div class="p-4 overflow-y-auto">
          <code class="!whitespace-pre-wrap">
            {{ props.response }}
          </code>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { InformationCircleOutline } from '@vicons/ionicons5';
import { KeyboardArrowDownRound, KeyboardArrowUpRound } from '@vicons/material';
import { ref } from 'vue';

const props = defineProps<{
  pluginName: string;
  request?: string;
  response?: string;
}>();

const expandContent = ref(false);

function handleExpand() {
  expandContent.value = !expandContent.value;
}
</script>

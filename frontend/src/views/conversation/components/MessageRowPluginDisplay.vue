<template>
  <div class="pt-2">
    <MessageRowPluginAction
      v-for="(action, i) in pluginActions"
      :key="i"
      :plugin-name="action.pluginName"
      :request="action.request"
      :response="action.response"
    />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { BaseChatMessage } from '@/types/schema';

import { PluginAction, splitPluginActions } from '../utils/message';
import MessageRowPluginAction from './MessageRowPluginAction.vue';

const props = defineProps<{
  messages: BaseChatMessage[];
}>();

const pluginActions = computed<PluginAction[]>(() => {
  if (!props.messages || props.messages.length === 0) return [];
  return splitPluginActions(props.messages);
});
</script>

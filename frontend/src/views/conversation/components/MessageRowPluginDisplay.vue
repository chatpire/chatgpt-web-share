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

import { BaseChatMessage, OpenaiWebChatMessageMetadata } from '@/types/schema';
import { getContentRawText } from '@/utils/chat';

import MessageRowPluginAction from './MessageRowPluginAction.vue';

const props = defineProps<{
  messages: BaseChatMessage[];
}>();

type PluginAction = {
  pluginName: string;
  request?: string;
  response?: string;
};

const pluginActions = computed<PluginAction[]>(() => {
  const result = [] as PluginAction[];
  // 每两条 message 是一个完整的 action
  // request: role == 'assistant'
  // response: role == 'tool'
  if (!props.messages) return [];
  for (let i = 0; i < props.messages.length; i += 2) {
    const requestMessage = props.messages[i];
    const responseMessage = props.messages[i + 1];
    if (!requestMessage || !responseMessage) continue;
    if (requestMessage.role == 'assistant' && responseMessage.role == 'tool') {
      const requestMeta = requestMessage.metadata as OpenaiWebChatMessageMetadata;
      result.push({
        pluginName: requestMeta.recipient || '',
        request: getContentRawText(requestMessage) || '',
        response: getContentRawText(responseMessage) || '',
      });
    }
  }
  return result;
});
</script>

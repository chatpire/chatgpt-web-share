import { useConversationStore } from '@/store';
import { ChatConversationDetail, ChatMessage } from '@/types/custom';

// 使用以下函数前需要确保调用了 conversationStore.fetchConversationHistory

export function getConvMessageListFromId(conversation_id: string | null) {
  const conversationStore = useConversationStore();
  const result = [];
  if (!conversation_id) return [];
  const conv: ChatConversationDetail = conversationStore.conversationDetailMap[conversation_id];
  if (conv) {
    let x = conv.current_node as any;
    while (x) {
      if (conv.mapping[x].message) result.push(conv.mapping[x]);
      x = conv.mapping[x].parent;
    }
    result.reverse();
  }
  return result;
}

export const getModelNameFromConv = (conv: ChatConversationDetail): string | null => {
  let result = null;
  let current_node = conv.current_node as any;
  while (current_node) {
    const node = conv.mapping[current_node];
    if (node.model_slug) {
      result = node.model_slug;
      break;
    }
    current_node = node.parent;
  }
  return result;
};

export const getModelNameFromMessages = (messages: Array<ChatMessage>): string | null => {
  let result = null;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i].model_slug) {
      result = messages[i].model_slug || null;
      break;
    }
  }
  return result;
};

export const getModelNameFromConvId = (conversation_id: string | null): string | null => {
  if (!conversation_id) return null;
  const conversationStore = useConversationStore();
  const conv: ChatConversationDetail = conversationStore.conversationDetailMap[conversation_id];
  if (conv) return getModelNameFromConv(conv);
  else return null;
};

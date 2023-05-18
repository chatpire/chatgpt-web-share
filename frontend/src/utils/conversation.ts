import { BaseChatMessage, BaseConversationHistory } from '@/types/schema';

export function getMessageListFromHistory(
  convHistory: BaseConversationHistory | undefined | null,
  lastNode: string | null = null
): BaseChatMessage[] {
  const result: BaseChatMessage[] = [];
  if (!convHistory) return result;
  let x = lastNode || convHistory.current_node || undefined;
  while (x != undefined) {
    const message = convHistory.mapping[x];
    if (message && message.content != undefined) {
      result.push(message);
      x = message.parent;
    } else {
      break;
    }
  }
  result.reverse();
  return result;
}

import { ChatMessage, ConversationHistoryDocument } from '@/types/schema';

export function getMessageListFromHistory(
  convHistory: ConversationHistoryDocument,
  lastNode: string | null = null
): ChatMessage[] {
  const result: ChatMessage[] = [];
  let x = lastNode || (convHistory.current_node as string | undefined);
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

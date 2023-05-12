import { ChatMessage, ConversationHistoryDocument } from '@/types/schema';

export function getMessageListFromHistory(
  convHistory: ConversationHistoryDocument | undefined,
  lastNode: string | null = null
): ChatMessage[] {
  const result: ChatMessage[] = [];
  if (convHistory == undefined) return result;
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

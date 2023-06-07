import { BaseChatMessage } from '@/types/schema';
import { getContentRawText } from '@/utils/chat';

// DisplayItem 表示由几条消息合并而来的一条消息，例如前面是若干次插件调用/browse，最后是正常的文本
interface BaseDisplayItem {
  type: 'text' | 'plugin_call' | 'browse_sequence';
  finishTime: string | undefined; // 最后一条消息的 create_time
}

interface DisplayItemText extends BaseDisplayItem {
  type: 'text';
  content: string;
  mergeCount: number; // 由几条消息合并而来
}

interface DisplayItemPluginCall extends BaseDisplayItem {
  type: 'plugin_call';
  requestContent: string | undefined;
  recipient: string | undefined;    // plugin_name.xxx
  responseContent: string | undefined;
}

type DisplayItem = DisplayItemText | DisplayItemPluginCall;

export function processDisplayItems(messages: BaseChatMessage[]) {
  const result: DisplayItem[] = [];
  let currentItem = null as DisplayItem | null;
  for (const message of messages) {
    if (message.source == 'openai_web') {
      if (!message || !message.content) continue;
      // 对于文本类型，合并连续内容
      if (typeof message.content == 'string' || message.content.content_type == 'text') {
        if (currentItem && currentItem.type == 'text') {
          currentItem.content += getContentRawText(message);
          currentItem.mergeCount += 1;
        } else {
          if (currentItem != null) result.push(currentItem);
          currentItem = { type: 'text', finishTime: message.create_time, content: getContentRawText(message), mergeCount: 1 };
        }
      }
    }
  }
  return result;
}
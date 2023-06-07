import { i18n } from '@/i18n';
import { allChatModelNames } from '@/types/json_schema';
import {
  BaseChatMessage,
  BaseConversationHistory,
  OpenaiApiChatMessageTextContent,
  OpenaiApiChatModels,
  OpenaiWebChatMessageCodeContent,
  OpenaiWebChatMessageMetadata,
  OpenaiWebChatMessageStderrContent,
  OpenaiWebChatMessageSystemErrorContent,
  OpenaiWebChatMessageTetherBrowsingDisplayContent,
  OpenaiWebChatMessageTetherQuoteContent,
  OpenaiWebChatMessageTextContent,
  OpenaiWebChatModels,
} from '@/types/schema';

const t = i18n.global.t as any;

export const chatModelColorMap: Record<string, string> = {
  gpt_3_5: 'green',
  gpt_3_5_mobile: 'darkgreen',
  gpt_4: 'purple',
  gpt_4_mobile: 'darkpurple',
  gpt_4_browsing: 'purple',
  gpt_4_plugins: 'purple',
};

export const getChatModelColor = (model_name: OpenaiWebChatModels | OpenaiApiChatModels | string | null) => {
  if (model_name && chatModelColorMap[model_name]) return chatModelColorMap[model_name];
  else return 'black';
};

export const getChatModelIconStyle = (model_name: OpenaiWebChatModels | OpenaiApiChatModels | string | null) => {
  if (model_name == 'gpt_4_plugins') return 'plugins';
  else if (model_name == 'gpt_4_browsing') return 'browsing';
  else return 'default';
};

export const getChatModelNameTrans = (model_name: OpenaiWebChatModels | OpenaiApiChatModels | string | null) => {
  if (model_name == null) return t('commons.unknown');
  if (allChatModelNames.includes(model_name)) return t(`models.${model_name}`);
  else return `${t('commons.unknown')}(${model_name})`;
  // else return model_name;
};

export const getCountTrans = (count: number | undefined | null): string => {
  if (count == undefined || count == null) return t('commons.unlimited');
  return count == -1 ? t('commons.unlimited') : `${count}`;
};

export const getContentRawText = (message: BaseChatMessage | null): string => {
  if (!message || !message.content) return '';
  if (typeof message.content == 'string') return message.content;
  else if (message.content.content_type == 'text') {
    if (message.source == 'openai_web') {
      const content = message.content as OpenaiWebChatMessageTextContent;
      return content.parts![0];
    } else {
      const content = message.content as OpenaiApiChatMessageTextContent;
      return content.text || '';
    }
  } else if (message.content.content_type == 'code') {
    const content = message.content as OpenaiWebChatMessageCodeContent;
    return content.text || '';
  } else if (message.content.content_type == 'stderr') {
    const content = message.content as OpenaiWebChatMessageStderrContent;
    return content.text || '';
  } else if (message.content.content_type == 'tether_browsing_display') {
    const content = message.content as OpenaiWebChatMessageTetherBrowsingDisplayContent;
    return content.result || '';
  } else if (message.content.content_type == 'tether_quote') {
    const content = message.content as OpenaiWebChatMessageTetherQuoteContent;
    return content.text || ''; // TODO: more info
  } else if (message.content.content_type == 'system_error') {
    const content = message.content as OpenaiWebChatMessageSystemErrorContent;
    return `${content.name}: ${content.text}`;
  } else {
    return `${message.content}`;
  }
};

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

// 用于按照连续消息分组，end_turn为true时截断
export function mergeContinuousMessages(messages: BaseChatMessage[]): BaseChatMessage[][] {
  const result = [] as BaseChatMessage[][];
  let currentMessageList = [] as BaseChatMessage[];
  for (const message of messages) {
    // 将chatgpt的连续对话划分到一组
    if (message.source == 'openai_web' && message.role !== 'user') {
      const metadata = message.metadata as OpenaiWebChatMessageMetadata;
      if (metadata && metadata.end_turn != true) {
        currentMessageList.push(message);
      } else {
        if (currentMessageList.length > 0) {
          currentMessageList.push(message);
          result.push(currentMessageList);
          currentMessageList = [];
        } else {
          result.push([message]);
        }
      }
    } else {
      // TODO: API 暂不支持连续对话合并
      if (currentMessageList.length > 0) {
        result.push(currentMessageList);
        currentMessageList = [];
      }
      result.push([message]);
    }
  }
  if (currentMessageList.length > 0) {
    result.push(currentMessageList);
  }
  return result;
}

// 对于一段连续消息中的消息按照功能性来分组

export function splitMessagesInGroup(messages: BaseChatMessage[]): BaseChatMessage[][] {
  const result = [] as BaseChatMessage[][];
  let currentMessageList = [] as BaseChatMessage[];
  let currentMessageListType: 'text' | 'other' | null = null;
  for (const message of messages) {
    if (message.source == 'openai_web') {
      const metadata = message.metadata as OpenaiWebChatMessageMetadata;
      // text: 连续的 content.content_type == "text" 且 recipient == 'all' 放到一组
      if (message.role == 'user') {
        if (messages.length > 1) {
          console.error('found multiple user message in splitMessagesInGroup', messages);
          continue;
        }
        currentMessageList.push(message);
        currentMessageListType = 'text';
      } else if (
        message.role == 'assistant' &&
        typeof message.content !== 'string' &&
        message.content?.content_type == 'text' &&
        metadata.recipient == 'all'
      ) {
        if (currentMessageListType !== 'text') {
          currentMessageListType = 'text';
          if (currentMessageList.length > 0) result.push(currentMessageList);
          currentMessageList = [];
        }
        currentMessageList.push(message);
        // 由于同一个对话中 plugins 调用和 browser 调用不能同时出现，因此连续的其它情况放到一组
      } else {
        if (currentMessageListType !== 'other') {
          if (currentMessageList.length > 0) result.push(currentMessageList);
          currentMessageListType = 'other';
          currentMessageList = [];
        }
        currentMessageList.push(message);
      }
    } else {
      // TODO: API 暂不支持连续对话合并
      if (currentMessageList.length > 0) {
        result.push(currentMessageList);
        currentMessageList = [];
      }
      result.push([message]);
    }
  }
  if (currentMessageList.length > 0) {
    result.push(currentMessageList);
  }
  return result;
}

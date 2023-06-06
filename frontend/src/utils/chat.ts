import {i18n} from '@/i18n';
import {allChatModelNames} from '@/types/json_schema';
import {
  BaseChatMessage,
  BaseConversationHistory,
  OpenaiApiChatMessageTextContent,
  OpenaiApiChatModels,
  OpenaiWebChatMessageCodeContent,
  OpenaiWebChatMessageMetadata,
  OpenaiWebChatMessageSystemErrorContent,
  OpenaiWebChatMessageTetherBrowsingDisplayContent,
  OpenaiWebChatMessageTetherQuoteContent,
  OpenaiWebChatMessageTextContent,
  OpenaiWebChatModels
} from '@/types/schema';

const t = i18n.global.t as any;

export const chatModelColorMap: Record<string, string> = {
  gpt_3_5: 'green',
  gpt_4: 'purple',
  gpt_4_mobile: 'darkblue',
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
  if (allChatModelNames.includes(model_name))
    return t(`models.${model_name}`);
  else
    return `${t('commons.unknown')}(${model_name})`;
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

export function mergeMessages(messages: BaseChatMessage[]): BaseChatMessage[][] {
  const result = [] as BaseChatMessage[][];
  let currentMessageList = [] as BaseChatMessage[];
  for (const message of messages) {
    if (message.role !== 'user' && message.source == 'openai_web') {
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
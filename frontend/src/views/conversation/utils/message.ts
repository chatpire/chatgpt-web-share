import { getFileDownloadUrlApi, getInterpreterSandboxFileDownloadUrlApi } from '@/api/conv';
import { i18n } from '@/i18n';
import {
  BaseChatMessage,
  ChatSourceTypes,
  OpenaiApiChatMessage,
  OpenaiApiChatMessageTextContent,
  OpenaiWebAskAttachment,
  OpenaiWebChatMessage,
  OpenaiWebChatMessageMetadata,
  OpenaiWebChatMessageMetadataCiteData,
  OpenaiWebChatMessageMultimodalTextContent,
  OpenaiWebChatMessageMultimodalTextContentImagePart,
  OpenaiWebChatMessageTextContent,
} from '@/types/schema';
import { getContentRawText, getTextMessageContent } from '@/utils/chat';
import { Dialog } from '@/utils/tips';

const t = i18n.global.t as any;

export type DisplayItemType =
  | 'text'
  | 'browser'
  | 'plugin'
  | 'code'
  | 'execution_output'
  | 'multimodal_text'
  | 'dalle_prompt'
  | 'dalle_result'
  | null;

export type DisplayItem = {
  type: DisplayItemType;
  messages: BaseChatMessage[];
};

export type PluginAction = {
  pluginName: string;
  request?: string;
  response?: string;
};

export function determineMessageType(group: BaseChatMessage[]): DisplayItemType | null {
  // api 仅有 text 类型
  if (group[0].source == 'openai_api') {
    if (group[0].content?.content_type !== 'text') {
      console.error('wrong content type in openai_api message', group);
    }
    return 'text';
  }
  for (const message of group) {
    if (message.source !== 'openai_web') {
      console.error('wrong message mixed in non-text content group', group);
      return null;
    }
  }

  let displayType: DisplayItemType | null = null;
  for (const message of group) {
    const metadata = message.metadata as OpenaiWebChatMessageMetadata;
    if (message.role == 'assistant' && message.model == 'gpt_4_plugins' && metadata.recipient !== 'all') {
      displayType = 'plugin';
    } else if (message.role == 'assistant' && message.model == 'gpt_4_browsing') {
      displayType = 'browser';
    } else if (message.content?.content_type == 'code') {
      displayType = 'code';
    } else if (message.content?.content_type == 'execution_output') {
      displayType = 'execution_output';
    } else if (
      message.role == 'assistant' &&
      message.metadata?.source == 'openai_web' &&
      message.metadata.recipient == 'dalle.text2im'
    ) {
      displayType = 'dalle_prompt';
    } else if (message.author_name == 'dalle.text2im') {
      displayType = 'dalle_result';
    } else if (message.content?.content_type == 'text') {
      displayType = 'text';
    } else if (message.content?.content_type == 'multimodal_text') {
      displayType = 'multimodal_text';
    }
    if (displayType) break;
  }

  if (!displayType) console.error('cannot find display type for group', group);
  return displayType;
}

export function buildTemporaryMessage(
  source: ChatSourceTypes,
  role: string,
  text_content: string,
  parent: string | undefined,
  model: string | undefined,
  openaiWebAttachments: OpenaiWebAskAttachment[] | null = null,
  openaiWebMultimodalImageParts: OpenaiWebChatMessageMultimodalTextContentImagePart[] | null = null
) {
  const random_strid = Math.random().toString(36).substring(2, 16);
  const result = {
    id: `temp_${random_strid}`,
    source,
    content: {
      content_type: 'text',
      parts: [text_content],
    },
    role: role,
    parent, // 其实没有用到parent
    children: [],
    model,
  } as BaseChatMessage;
  if (openaiWebAttachments) {
    const metadata = {
      attachments: openaiWebAttachments,
    } as OpenaiWebChatMessageMetadata;
    result.metadata = metadata;
  }
  if (openaiWebMultimodalImageParts) {
    result.content = {
      parts: [...openaiWebMultimodalImageParts, text_content],
    } as OpenaiWebChatMessageMultimodalTextContent;
  }
  return result;
}

export function modifiyTemporaryMessageContent(message: BaseChatMessage, textContent: string) {
  if (message.content?.content_type != 'text') {
    console.error('wrong content type in temporary openai_api message', message);
    return message.content;
  }
  if (message.source == 'openai_api') {
    const content = message.content as OpenaiApiChatMessageTextContent;
    content.text = textContent;
    return content;
  } else if (message.source == 'openai_web') {
    const content = message.content as OpenaiWebChatMessageTextContent;
    content.parts = [textContent];
    return content;
  }
  return message.content;
}

function htmlToElement(html: string) {
  const template = document.createElement('template');
  template.innerHTML = html.trim();
  return template.content.firstChild;
}

export function processCitations(contentDiv: HTMLDivElement) {
  const citationEls = contentDiv!.querySelectorAll('span.browsing-citation');
  const citationUrls = [] as string[];
  citationEls.forEach((el) => {
    const metadata = JSON.parse(
      decodeURIComponent(el.getAttribute('data-citation') || '')
    ) as OpenaiWebChatMessageMetadataCiteData;
    if (!metadata) return;
    let citationIndex = 0;
    if (citationUrls.includes(metadata.url!)) {
      citationIndex = citationUrls.indexOf(metadata.url!) + 1;
    } else {
      citationUrls.push(metadata.url!);
      citationIndex = citationUrls.length;
    }
    const newEl = htmlToElement(
      `<a href="${metadata.url!}" target="_blank" rel="noreferrer" class="px-0.5 text-green-600 !no-underline"><sup>${citationIndex}</sup></a>`
    );
    if (newEl) el.replaceWith(newEl);
  });
}

function findMessageIdOfSandboxFile(sandboxPath: string, messages: BaseChatMessage[]) {
  for (let i = 0; i < messages.length; i++) {
    const message = messages[i];
    const content = getTextMessageContent([message]);
    console.log(`search ${sandboxPath} in ${content}`);
    if (content.includes(sandboxPath)) {
      return message.id;
    }
  }
  return null;
}

function getSandboxLinkClickHandler(conversationId: string, messages: BaseChatMessage[]) {
  return (event: Event) => {
    const target = event.target as HTMLElement;

    if (target && target.matches('a.sandbox')) {
      event.preventDefault();

      // 设置元素禁止点击
      target.style.pointerEvents = 'none';

      const path = target.getAttribute('data-path');
      const messageId = findMessageIdOfSandboxFile(path!, messages);
      if (!path) return;
      if (!messageId) return;

      getInterpreterSandboxFileDownloadUrlApi(conversationId, messageId, path)
        .then((response) => {
          const url = response.data;
          window.open(url, '_blank');
        })
        .catch((e) => {
          console.error(e);
          if (e.message == 'errors.resourceNotFound') {
            Dialog.warning({
              content: t('tips.sandboxFileNotFound', [path]),
            });
          } else {
            Dialog.error({
              title: 'Error',
              content: t('tips.sandboxFileDownloadError'),
            });
          }
        })
        .finally(() => {
          target.style.pointerEvents = 'auto';
        });
    }
  };
}

export function processSandboxLinks(contentDiv: HTMLDivElement, conversationId: string, messages: BaseChatMessage[]) {
  const sandboxLinks = contentDiv.querySelectorAll('a[href^="sandbox:"]');

  sandboxLinks.forEach((link) => {
    link.classList.add('sandbox');
    const hrefValue = link.getAttribute('href');
    const path = hrefValue?.replace('sandbox:', '');
    link.setAttribute('data-path', path || '');
    const clickHandler = getSandboxLinkClickHandler(conversationId, messages);
    link.addEventListener('click', clickHandler);
  });
}

export async function getImageDownloadUrlFromFileServiceSchemaUrl(url: string | undefined) {
  if (!url || !url.startsWith('file-service://')) return null;
  try {
    const response = await getFileDownloadUrlApi(url.split('file-service://')[1]);
    return response.data;
  } catch (e) {
    console.error(e);
    return null;
  }
}

export function splitPluginActions (messages: BaseChatMessage[]) {
  const result = [] as PluginAction[];
  // 每两条 message 是一个完整的 action
  // request: role == 'assistant'
  // response: role == 'tool'
  for (let i = 0; i < messages.length; i += 2) {
    const requestMessage = messages[i];
    const responseMessage = messages[i + 1];
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
}


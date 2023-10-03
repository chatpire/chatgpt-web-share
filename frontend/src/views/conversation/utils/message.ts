import { getFileDownloadUrlApi, getInterpreterSandboxFileDownloadUrlApi } from '@/api/conv';
import { i18n } from '@/i18n';
import { BaseChatMessage, OpenaiWebChatMessageMetadataCiteData } from '@/types/schema';
import { getContentRawText, getTextMessageContent } from '@/utils/chat';
import { Dialog } from '@/utils/tips';

const t = i18n.global.t as any;

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
  recipient: string | undefined; // plugin_name.xxx
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
          currentItem = {
            type: 'text',
            finishTime: message.create_time,
            content: getContentRawText(message),
            mergeCount: 1,
          };
        }
      }
    }
  }
  return result;
}

export function htmlToElement(html: string) {
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
  }
  catch (e) {
    console.error(e);
    return null;
  }
}
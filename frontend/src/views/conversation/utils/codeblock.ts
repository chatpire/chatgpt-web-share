import * as clipboard from 'clipboard-polyfill';
import { Ref } from 'vue';

export function bindOnclick(contentRef: Ref<HTMLElement | undefined>) {
  // 获取模板引用中的所有 pre 元素和其子元素中的 button 元素
  const preElements = contentRef.value?.querySelectorAll('pre');
  if (!preElements) return;
  for (const preElement of preElements as any) {
    for (const button of preElement.querySelectorAll('button')) {
      (button as HTMLButtonElement).onmousedown = () => {
        // 如果按钮的内容为 "Copied!"，则跳过复制操作
        if (button.innerHTML === 'Copied!') {
          return;
        }

        const preContent = button.parentElement!.cloneNode(true) as HTMLElement;
        preContent.removeChild(preContent.querySelector('button')!);

        // Remove the alert element if it exists in preContent
        const alertElement = preContent.querySelector('.hljs-copy-alert');
        if (alertElement) {
          preContent.removeChild(alertElement);
        }

        clipboard
          .writeText(preContent.textContent || '')
          .then(function () {
            button.innerHTML = 'Copied!';
            button.dataset.copied = 'true';

            let alert: HTMLDivElement | null = Object.assign(document.createElement('div'), {
              role: 'status',
              className: 'hljs-copy-alert',
              innerHTML: 'Copied to clipboard',
            });
            button.parentElement!.appendChild(alert);

            setTimeout(() => {
              if (alert) {
                button.innerHTML = 'Copy';
                button.dataset.copied = 'false';
                button.parentElement!.removeChild(alert);
                alert = null;
              }
            }, 2000);
          })
          .then();
      };
    }
  }
}

// 为代码块设置样式以及添加copy按钮
export function processPreTags(htmlString: string, codeAutoWrap = false): string {
  // Parse the HTML string into an Element object.
  const parser = new DOMParser();
  const doc = parser.parseFromString(htmlString, 'text/html');

  // Get all the <pre> elements in the document.
  const preTags = doc.getElementsByTagName('pre');

  // Loop through the <pre> elements and add a <button> to each one.
  for (let i = 0; i < preTags.length; i++) {
    const preTag = preTags[i];

    const button = Object.assign(document.createElement('button'), {
      innerHTML: '',
      className: 'hljs-copy-button hide-in-print',
    });
    button.dataset.copied = 'false';
    preTag.classList.add('hljs-copy-wrapper');

    // Add a custom proprety to the code block so that the copy button can reference and match its background-color value.
    preTag.style.setProperty('--hljs-theme-background', window.getComputedStyle(preTag).backgroundColor);

    if (codeAutoWrap) {
      preTag.style.cssText += 'white-space: pre-wrap; word-wrap: break-word; word-break: break-all;';
    }

    preTag.appendChild(button);
  }

  // Serialize the modified Element object back into a string.
  const serializer = new XMLSerializer();
  return serializer.serializeToString(doc.documentElement);
}

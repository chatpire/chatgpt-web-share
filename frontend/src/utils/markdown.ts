import MarkdownIt from 'markdown-it';
import markdownItHighlight from 'markdown-it-highlightjs';

import hljs from './highlight';
import markdownItKatex from './markdown-it-katex';

const md = new MarkdownIt({
  html: true,
  linkify: false,
  typographer: true,
})
  .use(markdownItKatex)
  .use(markdownItHighlight, { hljs });

export default md;

import MarkdownIt from "markdown-it";
import markdownItHighlight from "markdown-it-highlightjs";
import markdownItMathjax3 from "markdown-it-mathjax3";
import hljs from "highlight.js";

const md = new MarkdownIt({
  html: true,
  linkify: false,
  typographer: true,
})
  .use(markdownItMathjax3)
  .use(markdownItHighlight, { hljs });

export default md;

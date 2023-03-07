import MarkdownIt from "markdown-it";
import markdownItKatex from "@traptitech/markdown-it-katex";
// import markdownItPrism from "markdown-it-prism";
import markdownItHighlight from "markdown-it-highlightjs";
import hljs from "highlight.js";

const md = new MarkdownIt({
  html: true,
  linkify: false,
  typographer: true,
})
  .use(markdownItKatex)
  .use(markdownItHighlight, { hljs });
// .use(markdownItPrism, { defaultLanguage: "python" });

export default md;

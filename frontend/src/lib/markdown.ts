import MarkdownIt from "markdown-it";

/**
 * Single parser instance for the whole app.
 *
 * `html: false` on purpose: rendered output goes through
 * `dangerouslySetInnerHTML`, so raw HTML in user-authored descriptions would be
 * a stored-XSS hole. Enable it only alongside a sanitizer.
 */
const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  typographer: true,
});

// External links open in a new tab, with the tab-nabbing protections.
const defaultLinkOpen =
  md.renderer.rules.link_open ??
  ((tokens, idx, options, _env, self) =>
    self.renderToken(tokens, idx, options));

md.renderer.rules.link_open = (tokens, idx, options, env, self) => {
  tokens[idx].attrSet("target", "_blank");
  tokens[idx].attrSet("rel", "noopener noreferrer");
  return defaultLinkOpen(tokens, idx, options, env, self);
};

/** Render a markdown source string to HTML. */
export function renderMarkdown(source: string): string {
  return md.render(source);
}

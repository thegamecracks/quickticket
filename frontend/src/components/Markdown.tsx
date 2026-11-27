import { useMemo } from 'react';
import { renderMarkdown } from '../lib/markdown';

type MarkdownProps = {
  content: string;
  className?: string;
};

/**
 * Renders trusted-but-unstyled markdown. Styling lives in `styles/markdown.css`
 * under the `.markdown` scope.
 */
export default function Markdown({ content, className = '' }: MarkdownProps) {
  const html = useMemo(() => renderMarkdown(content), [content]);

  // biome-ignore lint/security/noDangerouslySetInnerHtml: markdown-it is configured with html: false, so raw user HTML is escaped and only generated markup is emitted (see src/lib/markdown.ts)
  return <div className={`markdown ${className}`} dangerouslySetInnerHTML={{ __html: html }} />;
}

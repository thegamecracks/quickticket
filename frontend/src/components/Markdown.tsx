import { useMemo } from "react";
import { renderMarkdown } from "../lib/markdown";

type MarkdownProps = {
  content: string;
  className?: string;
};

/**
 * Renders trusted-but-unstyled markdown. Styling lives in `styles/markdown.css`
 * under the `.markdown` scope.
 */
export default function Markdown({ content, className = "" }: MarkdownProps) {
  const html = useMemo(() => renderMarkdown(content), [content]);

  return (
    <div
      className={`markdown ${className}`}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

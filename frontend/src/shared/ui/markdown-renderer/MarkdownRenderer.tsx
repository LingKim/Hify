import Markdown, { type Components } from "react-markdown";
import remarkGfm from "remark-gfm";

export interface MarkdownRendererProps {
  content: string;
  className?: string;
}

const markdownComponents: Components = {
  a({ children, href, ...props }) {
    return (
      <a href={href} rel="noreferrer" target="_blank" {...props}>
        {children}
      </a>
    );
  },
  table({ children, ...props }) {
    return (
      <div className="markdown-renderer-table-scroll">
        <table {...props}>{children}</table>
      </div>
    );
  },
  code({ children, className, ...props }) {
    return (
      <code className={className} {...props}>
        {children}
      </code>
    );
  },
};

export function MarkdownRenderer({
  content,
  className,
}: MarkdownRendererProps): JSX.Element {
  return (
    <div className={`markdown-renderer${className ? ` ${className}` : ""}`}>
      <Markdown components={markdownComponents} remarkPlugins={[remarkGfm]}>
        {content}
      </Markdown>
    </div>
  );
}

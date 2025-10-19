import { Components } from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

export const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  code: ({ className, children }) => {
    // Check if this is a code block (has language class) vs inline code
    const match = /language-(\w+)/.exec(className || '');

    if (match) {
      // Code block with syntax highlighting
      return (
        <SyntaxHighlighter
          PreTag="div"
          language={match[1]}
          style={vscDarkPlus}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      );
    }

    // Inline code
    const isInline = !className;
    return isInline ? (
      <code className="bg-primary/20 text-foreground px-1.5 py-0.5 rounded text-sm font-mono border border-primary/30">
        {children}
      </code>
    ) : (
      <code className="block bg-primary/20 text-foreground p-3 rounded my-2 text-sm font-mono overflow-x-auto border border-primary/30">
        {children}
      </code>
    );
  },
  ul: ({ children }) => (
    <ul className="list-disc list-inside mb-2 space-y-1" role="list">
      {children}
    </ul>
  ),
  ol: ({ children }) => (
    <ol className="list-decimal list-inside mb-2 space-y-1" role="list">
      {children}
    </ol>
  ),
  li: ({ children }) => <li className="ml-2">{children}</li>,
  h1: ({ children }) => (
    <h1 className="text-xl font-bold mb-2 mt-3" role="heading" aria-level={1}>
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="text-lg font-bold mb-2 mt-3" role="heading" aria-level={2}>
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="text-base font-bold mb-2 mt-2" role="heading" aria-level={3}>
      {children}
    </h3>
  ),
  strong: ({ children }) => (
    <strong className="font-bold text-foreground">
      {children}
    </strong>
  ),
  em: ({ children }) => <em className="italic">{children}</em>,
  blockquote: ({ children }) => (
    <blockquote
      className="border-l-4 border-primary/50 pl-4 my-2 italic text-muted-foreground"
      role="blockquote"
    >
      {children}
    </blockquote>
  ),
  a: ({ href, children }) => (
    <a
      href={href}
      className="text-primary hover:underline focus:underline"
      target="_blank"
      rel="noopener noreferrer"
      aria-label={`${children} (opens in new tab)`}
    >
      {children}
    </a>
  ),
};
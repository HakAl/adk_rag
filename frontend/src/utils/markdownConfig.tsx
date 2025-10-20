import { Components } from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

/**
 * Validates URL to prevent javascript:, data:, and vbscript: protocols
 */
const isValidUrl = (url: string | undefined): boolean => {
  if (!url) return false;

  const trimmed = url.trim().toLowerCase();
  const dangerousProtocols = ['javascript:', 'data:', 'vbscript:', 'file:', 'about:'];

  return !dangerousProtocols.some(protocol => trimmed.startsWith(protocol));
};

/**
 * Sanitizes language string for syntax highlighter
 */
const sanitizeLanguage = (lang: string): string => {
  // Only allow alphanumeric and common language identifiers
  return lang.replace(/[^a-zA-Z0-9+#-]/g, '');
};

export const markdownComponents: Components = {
  p: ({ children }) => <p className="mb-2 last:mb-0">{children}</p>,
  code: ({ className, children }) => {
    const match = /language-(\w+)/.exec(className || '');

    if (match) {
      const sanitizedLang = sanitizeLanguage(match[1]);
      const codeContent = String(children).replace(/\n$/, '');

      return (
        <SyntaxHighlighter
          PreTag="div"
          language={sanitizedLang}
          style={vscDarkPlus}
        >
          {codeContent}
        </SyntaxHighlighter>
      );
    }

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
  a: ({ href, children }) => {
    // SECURITY FIX: Validate URL before rendering
    if (!isValidUrl(href)) {
      return <span className="text-muted-foreground">{children}</span>;
    }

    return (
      <a
        href={href}
        className="text-primary hover:underline focus:underline"
        target="_blank"
        rel="noopener noreferrer"
        aria-label={`${children} (opens in new tab)`}
      >
        {children}
      </a>
    );
  },
  // SECURITY FIX: Disable potentially dangerous elements
  img: () => null,
  script: () => null,
  iframe: () => null,
  object: () => null,
  embed: () => null,
};
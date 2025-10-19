import { Bot } from 'lucide-react';
import { RoutingInfo } from '../api/chat';
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';

interface StreamingMessageProps {
  content: string;
  routingInfo: RoutingInfo | null;
  isStreaming?: boolean;
}

export const StreamingMessage = ({ content, routingInfo, isStreaming = true }: StreamingMessageProps) => {
  return (
    <div className="flex justify-start gap-1 sm:gap-2 animate-fade-in">
      <div className="glass-avatar bg-gradient-to-br from-primary to-accent text-primary-foreground rounded-full p-1.5 sm:p-2 h-7 w-7 sm:h-8 sm:w-8 flex items-center justify-center flex-shrink-0">
        <Bot className="h-3.5 w-3.5 sm:h-4 sm:w-4" aria-hidden="true" />
      </div>

      <div className="flex-1 space-y-2">
        {/* Routing Info Badge */}
        {routingInfo && (
          <div
            className="glass-message bg-primary/20 text-primary-foreground rounded-lg px-3 py-1.5 inline-flex items-center gap-2 text-xs sm:text-sm animate-fade-in"
            role="status"
            aria-live="polite"
          >
            <span className="font-medium">🎯 {routingInfo.agent_name}</span>
            <span className="opacity-75">•</span>
            <span className="opacity-90">{Math.round(routingInfo.confidence * 100)}%</span>
          </div>
        )}

        {/* Streaming Content */}
        <div
          className="glass-message bg-secondary/30 text-secondary-foreground rounded-lg px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base"
          role="status"
          aria-live="polite"
          aria-atomic="false"
        >
          {content ? (
            isStreaming ? (
              <pre className="whitespace-pre-wrap font-sans m-0">{content}</pre>
            ) : (
              <div className="markdown-content prose prose-sm sm:prose-base max-w-none">
                <ReactMarkdown
                  components={{
                    code(props) {
                      const { children, className } = props;
                      const match = /language-(\w+)/.exec(className || '');
                      return match ? (
                        <SyntaxHighlighter
                          PreTag="div"
                          language={match[1]}
                          style={vscDarkPlus}
                        >
                          {String(children).replace(/\n$/, '')}
                        </SyntaxHighlighter>
                      ) : (
                        <code className={className}>
                          {children}
                        </code>
                      );
                    }
                  }}
                >
                  {content}
                </ReactMarkdown>
              </div>
            )
          ) : (
            <span className="opacity-75 animate-pulse">Generating response...</span>
          )}
          {/* Cursor indicator */}
          {isStreaming && <span className="inline-block w-1.5 h-4 bg-primary ml-0.5 animate-pulse" aria-hidden="true" />}
        </div>
      </div>
    </div>
  );
};
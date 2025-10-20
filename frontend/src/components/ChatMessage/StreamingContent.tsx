import ReactMarkdown from 'react-markdown';
import { markdownComponents } from '../../utils/markdownConfig';

interface StreamingContentProps {
  content: string;
  isStreaming: boolean;
}

export const StreamingContent = ({ content, isStreaming }: StreamingContentProps) => {
  if (!content) {
    return (
      <span className="opacity-75 animate-pulse">Generating response...</span>
    );
  }

  if (isStreaming) {
    return (
      <>
        <pre className="whitespace-pre-wrap font-sans m-0">{content}</pre>
        <span
          className="inline-block w-1.5 h-4 bg-primary ml-0.5 animate-pulse"
          aria-hidden="true"
          aria-label="Typing indicator"
        />
      </>
    );
  }

  return (
    <div className="markdown-content prose prose-sm sm:prose-base max-w-none">
      <ReactMarkdown
        components={markdownComponents}
        disallowedElements={['script', 'iframe', 'object', 'embed', 'style']}
        unwrapDisallowed={true}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};
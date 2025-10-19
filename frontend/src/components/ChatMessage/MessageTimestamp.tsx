import { useMessageFormatting } from '../../hooks/useMessageFormatting';

interface MessageTimestampProps {
  timestamp: number;
}

export const MessageTimestamp = ({ timestamp }: MessageTimestampProps) => {
  const { formatTimestamp } = useMessageFormatting();

  return (
    <span className="text-xs text-muted-foreground px-1">
      <time dateTime={new Date(timestamp).toISOString()}>
        {formatTimestamp(timestamp)}
      </time>
    </span>
  );
};
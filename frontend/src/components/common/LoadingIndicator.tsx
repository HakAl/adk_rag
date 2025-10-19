interface LoadingIndicatorProps {
  message?: string;
  className?: string;
}

export const LoadingIndicator = ({
  message = 'Loading...',
  className = ''
}: LoadingIndicatorProps) => {
  return (
    <p
      className={`text-muted-foreground text-sm ${className}`}
      role="status"
      aria-live="polite"
    >
      {message}
    </p>
  );
};
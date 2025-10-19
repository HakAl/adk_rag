export const DATE_FORMAT_THRESHOLDS = {
  TODAY: 0,
  YESTERDAY: 1,
  RECENT_DAYS: 7,
} as const;

/**
 * Formats a timestamp into a human-readable relative date string
 * @param timestamp - Unix timestamp in milliseconds
 * @returns Formatted date string (e.g., "Today", "Yesterday", "3 days ago", or absolute date)
 */
export const formatSessionDate = (timestamp: number): string => {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const days = Math.floor(diff / (1000 * 60 * 60 * 24));

  if (days === DATE_FORMAT_THRESHOLDS.TODAY) return 'Today';
  if (days === DATE_FORMAT_THRESHOLDS.YESTERDAY) return 'Yesterday';
  if (days < DATE_FORMAT_THRESHOLDS.RECENT_DAYS) return `${days} days ago`;

  return date.toLocaleDateString();
};
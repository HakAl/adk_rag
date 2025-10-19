import { format } from 'date-fns';

export const useMessageFormatting = () => {
  const formatTimestamp = (timestamp: number): string => {
    return format(new Date(timestamp), 'h:mm a');
  };

  return { formatTimestamp };
};
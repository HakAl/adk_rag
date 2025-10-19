/**
 * Formats a confidence value (0-1) to a percentage string
 * @param confidence - Confidence value between 0 and 1
 * @returns Formatted percentage string (e.g., "95%")
 */
export const formatConfidence = (confidence: number): string => {
  return `${Math.round(confidence * 100)}%`;
};
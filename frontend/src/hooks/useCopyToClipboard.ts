import { useState, useCallback } from 'react';

export const useCopyToClipboard = () => {
  const [copiedId, setCopiedId] = useState<string | null>(null);

  const copyToClipboard = useCallback(async (id: string, text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedId(id);
      setTimeout(() => setCopiedId(null), 2000);
    } catch (err) {
      console.error('Failed to copy text:', err);
    }
  }, []);

  return { copiedId, copyToClipboard };
};
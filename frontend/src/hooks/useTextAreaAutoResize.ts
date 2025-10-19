import { useEffect, RefObject } from 'react';

interface TextareaHeights {
  mobile: { minHeight: number; maxHeight: number };
  desktop: { minHeight: number; maxHeight: number };
}

const DEFAULT_HEIGHTS: TextareaHeights = {
  mobile: { minHeight: 60, maxHeight: 150 },
  desktop: { minHeight: 80, maxHeight: 200 }
};

/**
 * Hook to automatically resize textarea based on content
 * @param textareaRef - Reference to the textarea element
 * @param content - Content that triggers resize (usually the input value)
 * @param heights - Optional custom height configuration
 */
export const useTextareaAutoResize = (
  textareaRef: RefObject<HTMLTextAreaElement>,
  content: string,
  heights: TextareaHeights = DEFAULT_HEIGHTS
) => {
  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Reset height to auto to get the correct scrollHeight
    textarea.style.height = 'auto';

    // Set height based on content, respecting min and max
    const scrollHeight = textarea.scrollHeight;
    const isMobile = window.innerWidth < 640;

    const { minHeight, maxHeight } = isMobile ? heights.mobile : heights.desktop;
    const newHeight = Math.min(Math.max(scrollHeight, minHeight), maxHeight);

    textarea.style.height = `${newHeight}px`;
  }, [content, textareaRef, heights]);
};
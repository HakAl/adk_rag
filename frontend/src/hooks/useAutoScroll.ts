import { useRef, useEffect, RefObject } from 'react';

interface UseAutoScrollOptions {
  enabled?: boolean;
  dependencies: any[];
}

export const useAutoScroll = ({
  enabled = true,
  dependencies
}: UseAutoScrollOptions): RefObject<HTMLDivElement> => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!enabled) return;

    if (scrollRef.current) {
      scrollRef.current.scrollTo({
        top: scrollRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  }, dependencies);

  return scrollRef;
};
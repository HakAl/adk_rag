import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown } from 'lucide-react';

interface CollapsibleProps {
  title: string;
  children: React.ReactNode;
  defaultOpen?: boolean;
}

export const Collapsible = ({ title, children, defaultOpen = false }: CollapsibleProps) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const contentRef = useRef<HTMLDivElement>(null);
  const [height, setHeight] = useState<number | undefined>(defaultOpen ? undefined : 0);

  useEffect(() => {
    if (contentRef.current) {
      setHeight(isOpen ? contentRef.current.scrollHeight : 0);
    }
  }, [isOpen]);

  return (
    <div className="border-b border-border last:border-b-0">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-4 hover:bg-secondary/20 transition-colors"
        aria-expanded={isOpen}
        aria-controls={`collapsible-content-${title.replace(/\s+/g, '-')}`}
      >
        <span className="font-medium text-foreground text-sm sm:text-base">{title}</span>
        <ChevronDown
          className={`h-4 w-4 sm:h-5 sm:w-5 transition-transform duration-200 text-muted-foreground ${
            isOpen ? 'rotate-180' : ''
          }`}
          aria-hidden="true"
        />
      </button>
      <div
        id={`collapsible-content-${title.replace(/\s+/g, '-')}`}
        ref={contentRef}
        style={{ height }}
        className="overflow-hidden transition-all duration-200 ease-in-out"
      >
        <div className="p-4 pt-0">{children}</div>
      </div>
    </div>
  );
};
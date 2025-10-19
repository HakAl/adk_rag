import { ReactNode } from 'react';
import { Card } from '../ui/card';

export type PanelSide = 'left' | 'right';

interface SlideInPanelProps {
  isOpen: boolean;
  onClose: () => void;
  side?: PanelSide;
  children: ReactNode;
  showOverlay?: boolean;
  width?: string;
}

export const SlideInPanel = ({
  isOpen,
  onClose,
  side = 'left',
  children,
  showOverlay = true,
  width = 'w-full sm:w-80 lg:w-96',
}: SlideInPanelProps) => {
  const sideStyles = {
    left: {
      position: 'left-0',
      translate: isOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      border: 'border-r',
      responsive: 'lg:relative',
    },
    right: {
      position: 'right-0',
      translate: isOpen ? 'translate-x-0' : 'translate-x-full',
      border: 'border-l',
      responsive: 'lg:absolute',
    },
  };

  const styles = sideStyles[side];

  return (
    <>
      {/* Mobile overlay */}
      {showOverlay && isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Panel - Slides in from specified side */}
      <aside
        className={`
          fixed ${styles.responsive} inset-y-0 ${styles.position} z-50
          ${width}
          transform transition-transform duration-200 ease-in-out
          ${styles.translate}
        `}
        aria-label={`${side} panel`}
        role="dialog"
        aria-modal="true"
      >
        <Card className={`h-full flex flex-col glass-card ${styles.border}`}>
          {children}
        </Card>
      </aside>
    </>
  );
};
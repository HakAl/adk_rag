import { X } from 'lucide-react';
import { Button } from '../ui/button';

interface SettingsPanelHeaderProps {
  onClose: () => void;
}

export const SettingsPanelHeader = ({ onClose }: SettingsPanelHeaderProps) => {
  return (
    <div className="p-3 sm:p-4 border-b flex items-center justify-between flex-shrink-0">
      <h2 className="text-base sm:text-lg font-semibold gradient-text">
        Settings
      </h2>
      <Button
        variant="ghost"
        size="icon"
        onClick={onClose}
        className="h-9 w-9 sm:h-10 sm:w-10 hover:bg-red-500/20 hover:text-red-400 transition-colors"
        aria-label="Close settings panel"
      >
        <X className="h-5 w-5" aria-hidden="true" />
      </Button>
    </div>
  );
};
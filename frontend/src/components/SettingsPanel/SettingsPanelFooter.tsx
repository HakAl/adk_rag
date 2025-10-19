import { RotateCcw } from 'lucide-react';
import { Button } from '../ui/button';

interface SettingsPanelFooterProps {
  onReset: () => void;
}

export const SettingsPanelFooter = ({ onReset }: SettingsPanelFooterProps) => {
  const handleReset = () => {
    if (window.confirm('Reset all settings to default?')) {
      onReset();
    }
  };

  return (
    <div className="p-3 sm:p-4 border-t flex-shrink-0">
      <Button
        variant="outline"
        onClick={handleReset}
        className="w-full flex items-center justify-center gap-2 h-11 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/50 transition-colors"
        aria-label="Reset all settings to default"
      >
        <RotateCcw className="h-4 w-4" aria-hidden="true" />
        Reset to Default
      </Button>
    </div>
  );
};
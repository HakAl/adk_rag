import { X, Moon, Sun, Type, RotateCcw } from 'lucide-react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Collapsible } from './ui/collapsible';
import { Theme, FontSize, Settings } from '../hooks/useSettings';

interface HealthResponse {
  status: string;
  version: string;
}

interface SettingsPanelProps {
  settings: Settings;
  onThemeChange: (theme: Theme) => void;
  onFontSizeChange: (fontSize: FontSize) => void;
  onReset: () => void;
  isOpen: boolean;
  onClose: () => void;
  health: HealthResponse | null;
}

export const SettingsPanel = ({
  settings,
  onThemeChange,
  onFontSizeChange,
  onReset,
  isOpen,
  onClose,
  health,
}: SettingsPanelProps) => {
  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-40 lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      {/* Settings Panel - Slides in from right */}
      <aside
        className={`
          fixed lg:absolute inset-y-0 right-0 z-50
          w-full sm:w-80 lg:w-96
          transform transition-transform duration-200 ease-in-out
          ${isOpen ? 'translate-x-0' : 'translate-x-full'}
        `}
        aria-label="Settings panel"
        role="dialog"
        aria-modal="true"
      >
        <Card className="h-full flex flex-col glass-card border-l">
          {/* Header */}
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

          {/* Settings Content */}
          <div className="flex-1 overflow-y-auto">
            {/* Theme Settings */}
            <Collapsible title="Appearance" defaultOpen={true}>
              <div className="space-y-3">
                <label className="text-sm text-muted-foreground block">
                  Theme
                </label>
                <div className="flex gap-2">
                  <Button
                    variant={settings.theme === 'light' ? 'default' : 'outline'}
                    className={`flex-1 flex items-center justify-center gap-2 h-11 ${
                      settings.theme === 'light' ? 'glass-button' : ''
                    }`}
                    onClick={() => onThemeChange('light')}
                    aria-label="Switch to light theme"
                    aria-pressed={settings.theme === 'light'}
                  >
                    <Sun className="h-4 w-4" aria-hidden="true" />
                    Light
                  </Button>
                  <Button
                    variant={settings.theme === 'dark' ? 'default' : 'outline'}
                    className={`flex-1 flex items-center justify-center gap-2 h-11 ${
                      settings.theme === 'dark' ? 'glass-button' : ''
                    }`}
                    onClick={() => onThemeChange('dark')}
                    aria-label="Switch to dark theme"
                    aria-pressed={settings.theme === 'dark'}
                  >
                    <Moon className="h-4 w-4" aria-hidden="true" />
                    Dark
                  </Button>
                </div>
              </div>
            </Collapsible>

            {/* Font Size Settings */}
            <Collapsible title="Text Size" defaultOpen={true}>
              <div className="space-y-3">
                <label className="text-sm text-muted-foreground block">
                  Font Size
                </label>
                <div className="flex flex-col gap-2">
                  <Button
                    variant={settings.fontSize === 'small' ? 'default' : 'outline'}
                    className={`w-full flex items-center justify-center gap-2 h-11 ${
                      settings.fontSize === 'small' ? 'glass-button' : ''
                    }`}
                    onClick={() => onFontSizeChange('small')}
                    aria-label="Set font size to small"
                    aria-pressed={settings.fontSize === 'small'}
                  >
                    <Type className="h-3 w-3" aria-hidden="true" />
                    <span className="text-sm">Small (14px)</span>
                  </Button>
                  <Button
                    variant={settings.fontSize === 'medium' ? 'default' : 'outline'}
                    className={`w-full flex items-center justify-center gap-2 h-11 ${
                      settings.fontSize === 'medium' ? 'glass-button' : ''
                    }`}
                    onClick={() => onFontSizeChange('medium')}
                    aria-label="Set font size to medium"
                    aria-pressed={settings.fontSize === 'medium'}
                  >
                    <Type className="h-4 w-4" aria-hidden="true" />
                    <span className="text-base">Medium (16px)</span>
                  </Button>
                  <Button
                    variant={settings.fontSize === 'large' ? 'default' : 'outline'}
                    className={`w-full flex items-center justify-center gap-2 h-11 ${
                      settings.fontSize === 'large' ? 'glass-button' : ''
                    }`}
                    onClick={() => onFontSizeChange('large')}
                    aria-label="Set font size to large"
                    aria-pressed={settings.fontSize === 'large'}
                  >
                    <Type className="h-5 w-5" aria-hidden="true" />
                    <span className="text-lg">Large (18px)</span>
                  </Button>
                </div>
              </div>
            </Collapsible>

            {/* About Section */}
            <Collapsible title="About">
              <div className="space-y-2 text-sm text-muted-foreground">
                <p>
                  <strong className="text-foreground">VIBE Agent</strong>
                </p>
                <p>Version: {process.env.REACT_APP_VERSION || '0.1.0'}</p>
                {health && (
                  <p role="status" aria-live="polite">
                    Status: <span className="text-green-500 font-semibold">{health.status}</span>
                  </p>
                )}
                <p className="text-xs mt-4">
                  Vibe coded development assistant.
                </p>
              </div>
            </Collapsible>
          </div>

          {/* Footer - Reset Button */}
          <div className="p-3 sm:p-4 border-t flex-shrink-0">
            <Button
              variant="outline"
              onClick={() => {
                if (window.confirm('Reset all settings to default?')) {
                  onReset();
                }
              }}
              className="w-full flex items-center justify-center gap-2 h-11 hover:bg-red-500/20 hover:text-red-400 hover:border-red-500/50 transition-colors"
              aria-label="Reset all settings to default"
            >
              <RotateCcw className="h-4 w-4" aria-hidden="true" />
              Reset to Default
            </Button>
          </div>
        </Card>
      </aside>
    </>
  );
};
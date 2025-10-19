import { Card } from '../ui/card';
import { SettingsPanelHeader } from './SettingsPanelHeader';
import { SettingsPanelFooter } from './SettingsPanelFooter';
import { ThemeSection } from './sections/ThemeSection';
import { FontSizeSection } from './sections/FontSizeSection';
import { AboutSection } from './sections/AboutSection';
import { Theme, FontSize, Settings } from '../../types/settings';

interface HealthResponse {
  status: string;
  version: string;
}

export interface SettingsPanelProps {
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
          <SettingsPanelHeader onClose={onClose} />

          {/* Settings Content */}
          <div className="flex-1 overflow-y-auto">
            <ThemeSection
              currentTheme={settings.theme}
              onThemeChange={onThemeChange}
            />

            <FontSizeSection
              currentFontSize={settings.fontSize}
              onFontSizeChange={onFontSizeChange}
            />

            <AboutSection health={health} />
          </div>

          <SettingsPanelFooter onReset={onReset} />
        </Card>
      </aside>
    </>
  );
};
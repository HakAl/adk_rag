import { SlideInPanel } from '../common/SlideInPanel';
import { SettingsPanelHeader } from './SettingsPanelHeader';
import { SettingsPanelFooter } from './SettingsPanelFooter';
import { ThemeSection } from './sections/ThemeSection';
import { FontSizeSection } from './sections/FontSizeSection';
import { AboutSection } from './sections/AboutSection';
import { Theme, FontSize, Settings } from '../../types/settings';
import { AppMode } from '../../config/mode';

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
  mode?: AppMode;
}

export const SettingsPanel = ({
  settings,
  onThemeChange,
  onFontSizeChange,
  onReset,
  isOpen,
  onClose,
  health,
  mode,
}: SettingsPanelProps) => {
  return (
    <SlideInPanel
      isOpen={isOpen}
      onClose={onClose}
      side="right"
    >
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

        <AboutSection health={health} mode={mode} />
      </div>

      <SettingsPanelFooter onReset={onReset} />
    </SlideInPanel>
  );
};
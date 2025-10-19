export type Theme = 'light' | 'dark';
export type FontSize = 'small' | 'medium' | 'large';

export interface Settings {
  theme: Theme;
  fontSize: FontSize;
}

export interface SettingsContextValue {
  settings: Settings;
  updateTheme: (theme: Theme) => void;
  updateFontSize: (fontSize: FontSize) => void;
  updateSettings: (partial: Partial<Settings>) => void;
  resetSettings: () => void;
}

export const SETTINGS_VERSION = 1;
export const STORAGE_KEY = 'vibe-agent-settings';

export const DEFAULT_SETTINGS: Settings = {
  theme: 'dark',
  fontSize: 'medium',
};

export const FONT_SIZE_MAP: Record<FontSize, string> = {
  small: '14px',
  medium: '16px',
  large: '18px',
};
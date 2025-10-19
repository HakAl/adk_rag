import { createContext, useState, useEffect, ReactNode } from 'react';
import {
  Settings,
  SettingsContextValue,
  Theme,
  FontSize,
  DEFAULT_SETTINGS,
  STORAGE_KEY,
  SETTINGS_VERSION,
  FONT_SIZE_MAP,
} from '../types/settings';

export const SettingsContext = createContext<SettingsContextValue | undefined>(undefined);

interface StoredSettings {
  version: number;
  data: Settings;
}

interface SettingsProviderProps {
  children: ReactNode;
}

export const SettingsProvider = ({ children }: SettingsProviderProps) => {
  const [settings, setSettings] = useState<Settings>(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed: StoredSettings = JSON.parse(stored);

        // Version check for future migrations
        if (parsed.version === SETTINGS_VERSION) {
          return parsed.data;
        }

        // If version mismatch, could add migration logic here
        console.warn('Settings version mismatch, using defaults');
      }
    } catch (error) {
      console.error('Failed to load settings:', error);
    }

    return DEFAULT_SETTINGS;
  });

  // Apply theme to document
  useEffect(() => {
    const root = document.documentElement;
    if (settings.theme === 'dark') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
  }, [settings.theme]);

  // Apply font size to document
  useEffect(() => {
    const root = document.documentElement;
    root.style.fontSize = FONT_SIZE_MAP[settings.fontSize];
  }, [settings.fontSize]);

  // Persist settings to localStorage
  useEffect(() => {
    try {
      const toStore: StoredSettings = {
        version: SETTINGS_VERSION,
        data: settings,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toStore));
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  }, [settings]);

  const updateTheme = (theme: Theme) => {
    setSettings((prev) => ({ ...prev, theme }));
  };

  const updateFontSize = (fontSize: FontSize) => {
    setSettings((prev) => ({ ...prev, fontSize }));
  };

  const updateSettings = (partial: Partial<Settings>) => {
    setSettings((prev) => ({ ...prev, ...partial }));
  };

  const resetSettings = () => {
    setSettings(DEFAULT_SETTINGS);
  };

  const value: SettingsContextValue = {
    settings,
    updateTheme,
    updateFontSize,
    updateSettings,
    resetSettings,
  };

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
};
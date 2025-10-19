import { Moon, Sun } from 'lucide-react';
import { Button } from '../../ui/button';
import { Collapsible } from '../../ui/collapsible';
import { Theme } from '../../../types/settings';
import { THEME_OPTIONS } from '../config/themeOptions';

interface ThemeSectionProps {
  currentTheme: Theme;
  onThemeChange: (theme: Theme) => void;
}

export const ThemeSection = ({ currentTheme, onThemeChange }: ThemeSectionProps) => {
  const icons = {
    light: Sun,
    dark: Moon,
  };

  return (
    <Collapsible title="Appearance" defaultOpen={true}>
      <div className="space-y-3">
        <label className="text-sm text-muted-foreground block">
          Theme
        </label>
        <div className="flex gap-2">
          {THEME_OPTIONS.map((option) => {
            const Icon = icons[option.value];
            const isActive = currentTheme === option.value;

            return (
              <Button
                key={option.value}
                variant={isActive ? 'default' : 'outline'}
                className={`flex-1 flex items-center justify-center gap-2 h-11 ${
                  isActive ? 'glass-button' : ''
                }`}
                onClick={() => onThemeChange(option.value)}
                aria-label={`Switch to ${option.label.toLowerCase()} theme`}
                aria-pressed={isActive}
              >
                <Icon className="h-4 w-4" aria-hidden="true" />
                {option.label}
              </Button>
            );
          })}
        </div>
      </div>
    </Collapsible>
  );
};
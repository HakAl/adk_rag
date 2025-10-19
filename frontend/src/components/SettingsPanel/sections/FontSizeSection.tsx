import { Type } from 'lucide-react';
import { Button } from '../../ui/button';
import { Collapsible } from '../../ui/collapsible';
import { FontSize } from '../../../types/settings';
import { FONT_SIZE_OPTIONS } from '../config/fontSizeOptions';

interface FontSizeSectionProps {
  currentFontSize: FontSize;
  onFontSizeChange: (fontSize: FontSize) => void;
}

export const FontSizeSection = ({
  currentFontSize,
  onFontSizeChange
}: FontSizeSectionProps) => {
  return (
    <Collapsible title="Text Size" defaultOpen={true}>
      <div className="space-y-3">
        <label className="text-sm text-muted-foreground block">
          Font Size
        </label>
        <div className="flex flex-col gap-2">
          {FONT_SIZE_OPTIONS.map((option) => {
            const isActive = currentFontSize === option.value;

            return (
              <Button
                key={option.value}
                variant={isActive ? 'default' : 'outline'}
                className={`w-full flex items-center justify-center gap-2 h-11 ${
                  isActive ? 'glass-button' : ''
                }`}
                onClick={() => onFontSizeChange(option.value)}
                aria-label={`Set font size to ${option.label.toLowerCase()}`}
                aria-pressed={isActive}
              >
                <Type className={option.iconSize} aria-hidden="true" />
                <span className={option.textSize}>{option.label}</span>
              </Button>
            );
          })}
        </div>
      </div>
    </Collapsible>
  );
};
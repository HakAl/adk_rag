import { FontSize } from '../../../types/settings';

export interface FontSizeOption {
  value: FontSize;
  label: string;
  iconSize: string;
  textSize: string;
}

export const FONT_SIZE_OPTIONS: FontSizeOption[] = [
  {
    value: 'small',
    label: 'Small (14px)',
    iconSize: 'h-3 w-3',
    textSize: 'text-sm'
  },
  {
    value: 'medium',
    label: 'Medium (16px)',
    iconSize: 'h-4 w-4',
    textSize: 'text-base'
  },
  {
    value: 'large',
    label: 'Large (18px)',
    iconSize: 'h-5 w-5',
    textSize: 'text-lg'
  },
];
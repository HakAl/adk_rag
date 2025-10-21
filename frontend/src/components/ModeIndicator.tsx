import { Server, Zap } from 'lucide-react';
import { Badge } from './ui/badge';
import { AppMode } from '../config/mode';

interface ModeIndicatorProps {
  mode: AppMode;
}

export const ModeIndicator = ({ mode }: ModeIndicatorProps) => {
  const isFullMode = mode === 'full';

  const modeConfig = {
    full: {
      label: 'Full Mode',
      icon: Server,
      description: 'Built with Google\'s Agent Development Kit (ADK), featuring intelligent routing, parallel specialist execution, and automatic provider fallback for rock-solid reliability.',
      bgClass: 'bg-green-500/90 hover:bg-green-500/80',
      borderClass: 'border-green-400/50',
    },
    lite: {
      label: 'Lite Mode',
      icon: Zap,
      description: 'Fast cloud API specialists that analyze, generate, and validate code with direct API connections.',
      bgClass: 'bg-purple-500/90 hover:bg-purple-500/80',
      borderClass: 'border-purple-400/50',
    },
  };

  const config = modeConfig[mode];
  const Icon = config.icon;

  return (
    <>
      <Badge
        className={`${config.bgClass} ${config.borderClass} text-white border transition-all duration-200`}
      >
        <Icon className="h-3 w-3 mr-1" aria-hidden="true" />
        {config.label}
      </Badge>
      <p className="text-xs text-muted-foreground leading-relaxed mt-1">
        {config.description}
      </p>
    </>
  );
};
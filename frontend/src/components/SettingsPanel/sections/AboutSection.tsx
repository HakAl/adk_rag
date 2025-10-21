import { Collapsible } from '../../ui/collapsible';
import { ModeIndicator } from '../../ModeIndicator';
import { AppMode } from '../../../config/mode';
import { Github } from 'lucide-react';

interface HealthResponse {
  status: string;
  version: string;
}

interface AboutSectionProps {
  health: HealthResponse | null;
  mode?: AppMode;
}

export const AboutSection = ({ health, mode }: AboutSectionProps) => {
  return (
    <Collapsible title="About">
      <div className="space-y-2 text-sm text-muted-foreground">
        <p>
          <strong className="text-foreground">VIBE Code</strong>
        </p>
        <p>Version: {import.meta.env.VITE_VERSION || '0.1.0'}</p>
        {mode && (
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span>Mode:</span>
              <ModeIndicator mode={mode} />
            </div>
          </div>
        )}
        {health && (
          <p role="status" aria-live="polite">
            Status: <span className="text-green-500 font-semibold">{health.status}</span>
          </p>
        )}
        <p className="text-xs mt-4">
          Vibe coded development assistant.
        </p>
        <a
          href="https://github.com/HakAl/adk_rag"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-2 text-sm text-primary hover:underline mt-2"
        >
          <Github className="h-4 w-4" />
          View on GitHub
        </a>
      </div>
    </Collapsible>
  );
};
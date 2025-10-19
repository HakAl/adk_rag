import { Collapsible } from '../../ui/collapsible';

interface HealthResponse {
  status: string;
  version: string;
}

interface AboutSectionProps {
  health: HealthResponse | null;
}

export const AboutSection = ({ health }: AboutSectionProps) => {
  return (
    <Collapsible title="About">
      <div className="space-y-2 text-sm text-muted-foreground">
        <p>
          <strong className="text-foreground">VIBE Agent</strong>
        </p>
        <p>Version: {import.meta.env.VITE_VERSION || '0.1.0'}</p>
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
  );
};
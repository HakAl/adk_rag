import { RoutingInfo } from '../../api/backend/chat.ts';
import { formatConfidence } from '../../utils/formatters';

interface RoutingBadgeProps {
  routingInfo: RoutingInfo;
}

export const RoutingBadge = ({ routingInfo }: RoutingBadgeProps) => {
  return (
    <div
      className="glass-message bg-primary/20 text-primary-foreground rounded-lg px-3 py-1.5 inline-flex items-center gap-2 text-xs sm:text-sm animate-fade-in"
      role="status"
      aria-live="polite"
      aria-label={`Routed to ${routingInfo.agent_name} agent with ${formatConfidence(routingInfo.confidence)} confidence`}
    >
      <span className="font-medium">🎯 {routingInfo.agent_name}</span>
      <span className="opacity-75">•</span>
      <span className="opacity-90">{formatConfidence(routingInfo.confidence)}</span>
    </div>
  );
};
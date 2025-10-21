import { Collapsible } from '../../ui/collapsible';
import { Trash2 } from 'lucide-react';

interface ClearApiKeysSectionProps {
  onClearKeys: () => void;
  hasKeys: boolean;
}

export const ClearApiKeysSection = ({ onClearKeys, hasKeys }: ClearApiKeysSectionProps) => {
  return (
    <Collapsible title="API Keys">
      <div className="space-y-2">
        <p className="text-sm text-muted-foreground">
          Remove stored API keys from memory.
        </p>
        <button
          onClick={onClearKeys}
          disabled={!hasKeys}
          className="flex items-center gap-2 px-4 py-2 text-sm bg-red-500/10 hover:bg-red-500/20 text-red-600 dark:text-red-400 rounded-md border border-red-500/20 transition-colors disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:bg-red-500/10"
        >
          <Trash2 className="h-4 w-4" />
          Clear API Keys
        </button>
      </div>
    </Collapsible>
  );
};
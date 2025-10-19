import { Settings as SettingsIcon } from 'lucide-react';
import { Button } from '../ui/button';
import { ErrorAlert } from '../common/ErrorAlert';
import { LoadingIndicator } from '../common/LoadingIndicator';

interface HeaderProps {
  loading: boolean;
  error: string | null;
  onSettingsClick: () => void;
  settingsOpen: boolean;
}

export const Header = ({
  loading,
  error,
  onSettingsClick,
  settingsOpen
}: HeaderProps) => {
  return (
    <header className="flex-shrink-0 border-b border-border">
      <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary">
            VIBE Agent
          </h1>

          <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
            <Button
              variant="ghost"
              size="icon"
              onClick={onSettingsClick}
              className="h-9 w-9 sm:h-10 sm:w-10"
              aria-label="Open settings"
              aria-expanded={settingsOpen}
            >
              <SettingsIcon className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />
            </Button>
          </div>
        </div>

        {loading && <LoadingIndicator className="mt-2" />}

        {error && <ErrorAlert message={error} className="mt-3 sm:mt-4" />}
      </div>
    </header>
  );
};
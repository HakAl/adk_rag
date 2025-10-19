import { ReactNode } from 'react';
import { Header } from './Header';

interface LayoutProps {
  children: ReactNode;
  loading: boolean;
  error: string | null;
  onSettingsClick: () => void;
  settingsOpen: boolean;
}

export const Layout = ({
  children,
  loading,
  error,
  onSettingsClick,
  settingsOpen
}: LayoutProps) => {
  return (
    <div className="h-screen bg-background flex flex-col">
      {/* Skip to main content link for keyboard navigation */}
      <a href="#main-content" className="skip-link">
        Skip to main content
      </a>

      <Header
        loading={loading}
        error={error}
        onSettingsClick={onSettingsClick}
        settingsOpen={settingsOpen}
      />

      <main
        id="main-content"
        className="flex-1 px-2 sm:px-4 py-2 sm:py-4 min-h-0 overflow-hidden relative"
      >
        {children}
      </main>
    </div>
  );
};
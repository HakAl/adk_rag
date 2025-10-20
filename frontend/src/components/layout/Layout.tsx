import { Header } from './Header';

interface LayoutProps {
  children: React.ReactNode;
  loading: boolean;
  error: string | null;
  onSettingsClick: () => void;
  onSettingsClose: () => void;
  settingsOpen: boolean;
}

export const Layout = ({
  children,
  loading,
  error,
  onSettingsClick,
  onSettingsClose,
  settingsOpen
}: LayoutProps) => {
  return (
    <div className="flex flex-col h-screen">
      <Header
        loading={loading}
        error={error}
        onSettingsClick={onSettingsClick}
        onSettingsClose={onSettingsClose}
        settingsOpen={settingsOpen}
      />
      <main className="flex-1 overflow-hidden p-3 sm:p-4 md:p-6">
        {children}
      </main>
    </div>
  );
};
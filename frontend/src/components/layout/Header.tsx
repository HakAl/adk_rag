import { useState, useRef, useEffect } from 'react';
import { Settings as SettingsIcon, LogOut, ChevronDown, User } from 'lucide-react';
import { Button } from '../ui/button';
import { ErrorAlert } from '../common/ErrorAlert';
import { LoadingIndicator } from '../common/LoadingIndicator';
import { useAuth } from '../../contexts/AuthContext';

interface HeaderProps {
  loading: boolean;
  error: string | null;
  onSettingsClick: () => void;
  onSettingsClose: () => void;
  settingsOpen: boolean;
}

export const Header = ({
  loading,
  error,
  onSettingsClick,
  onSettingsClose,
  settingsOpen
}: HeaderProps) => {
  const { user, logout } = useAuth();
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setDropdownOpen(false);
      }
    };

    if (dropdownOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [dropdownOpen]);

  // Close settings when dropdown opens
  useEffect(() => {
    if (dropdownOpen && settingsOpen) {
      onSettingsClose();
    }
  }, [dropdownOpen, settingsOpen, onSettingsClose]);

  const handleLogout = async () => {
    setDropdownOpen(false);
    await logout();
  };

  const handleSettings = () => {
    setDropdownOpen(false);
    onSettingsClick();
  };

  const handleDropdownToggle = () => {
    setDropdownOpen(!dropdownOpen);
  };

  const capitalizeUsername = (username: string) => {
    return username.charAt(0).toUpperCase() + username.slice(1);
  };

  return (
    <header className="flex-shrink-0 border-b border-border">
      <div className="container mx-auto px-3 sm:px-4 py-3 sm:py-4">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 sm:gap-0">
          <h1 className="text-xl sm:text-2xl md:text-3xl font-bold text-primary">
            VIBE Code
          </h1>

          <div className="flex items-center gap-3 sm:gap-4 flex-wrap">
            {user && (
              <div className="relative" ref={dropdownRef}>
                <Button
                  variant="ghost"
                  onClick={handleDropdownToggle}
                  className="flex items-center gap-2 h-9 sm:h-10"
                  aria-label="User menu"
                  aria-expanded={dropdownOpen}
                >
                  <User className="h-4 w-4 sm:h-5 sm:w-5" aria-hidden="true" />
                  <span className="text-sm sm:text-base">
                    Welcome, {capitalizeUsername(user.username)}
                  </span>
                  <ChevronDown
                    className={`h-4 w-4 transition-transform ${
                      dropdownOpen ? 'rotate-180' : ''
                    }`}
                    aria-hidden="true"
                  />
                </Button>

                {dropdownOpen && (
                  <div className="absolute right-0 mt-2 w-48 glass-card border border-border rounded-md shadow-lg z-50">
                    <div className="py-1">
                      <button
                        onClick={handleSettings}
                        className="w-full px-4 py-2 text-sm text-left hover:bg-muted/50 flex items-center gap-2"
                      >
                        <SettingsIcon className="h-4 w-4" aria-hidden="true" />
                        Settings
                      </button>
                      <button
                        onClick={handleLogout}
                        className="w-full px-4 py-2 text-sm text-left hover:bg-muted/50 flex items-center gap-2 text-red-500"
                      >
                        <LogOut className="h-4 w-4" aria-hidden="true" />
                        Sign Out
                      </button>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {loading && <LoadingIndicator className="mt-2" />}

        {error && <ErrorAlert message={error} className="mt-3 sm:mt-4" />}
      </div>
    </header>
  );
};
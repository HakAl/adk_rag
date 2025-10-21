import { createContext, useContext, useState, ReactNode } from 'react';
import { Provider } from '../api/direct/coordinator';

export interface ApiKeys {
  anthropic?: string;
  google?: string;
}

interface ApiKeyContextValue {
  keys: ApiKeys;
  provider: Provider;
  setApiKeys: (keys: Partial<ApiKeys>) => void;
  setProvider: (provider: Provider) => void;
  setAnthropicKey: (key: string) => void;
  setGoogleKey: (key: string) => void;
  clearKeys: () => void;
  clearApiKeys: () => void; // Alias for clearKeys
  hasAnthropicKey: () => boolean;
  hasGoogleKey: () => boolean;
  hasAnyKey: () => boolean;
  hasApiKeys: () => boolean; // Alias for hasAnyKey
}

const ApiKeyContext = createContext<ApiKeyContextValue | undefined>(undefined);

interface ApiKeyProviderProps {
  children: ReactNode;
}

export const ApiKeyProvider = ({ children }: ApiKeyProviderProps) => {
  const [keys, setKeys] = useState<ApiKeys>({
    anthropic: undefined,
    google: undefined,
  });

  // Get initial provider from sessionStorage or default to anthropic
  const [provider, setProviderState] = useState<Provider>(() => {
    const stored = sessionStorage.getItem('preferredProvider');
    return (stored === 'anthropic' || stored === 'google') ? stored : 'anthropic';
  });

  const setApiKeys = (newKeys: Partial<ApiKeys>) => {
    setKeys(prev => ({
      ...prev,
      ...Object.fromEntries(
        Object.entries(newKeys).map(([k, v]) => [k, v?.trim() || undefined])
      ),
    }));
  };

  const setProvider = (newProvider: Provider) => {
    setProviderState(newProvider);
    sessionStorage.setItem('preferredProvider', newProvider);
  };

  const setAnthropicKey = (key: string) => {
    setApiKeys({ anthropic: key });
  };

  const setGoogleKey = (key: string) => {
    setApiKeys({ google: key });
  };

  const clearKeys = () => {
    setKeys({
      anthropic: undefined,
      google: undefined,
    });
  };

  const hasAnthropicKey = (): boolean => {
    return keys.anthropic !== undefined && keys.anthropic.length > 0;
  };

  const hasGoogleKey = (): boolean => {
    return keys.google !== undefined && keys.google.length > 0;
  };

  const hasAnyKey = (): boolean => {
    return hasAnthropicKey() || hasGoogleKey();
  };

  const value: ApiKeyContextValue = {
    keys,
    provider,
    setApiKeys,
    setProvider,
    setAnthropicKey,
    setGoogleKey,
    clearKeys,
    clearApiKeys: clearKeys, // Alias
    hasAnthropicKey,
    hasGoogleKey,
    hasAnyKey,
    hasApiKeys: hasAnyKey, // Alias
  };

  return (
    <ApiKeyContext.Provider value={value}>
      {children}
    </ApiKeyContext.Provider>
  );
};

export const useApiKeys = (): ApiKeyContextValue => {
  const context = useContext(ApiKeyContext);
  if (context === undefined) {
    throw new Error('useApiKeys must be used within an ApiKeyProvider');
  }
  return context;
};
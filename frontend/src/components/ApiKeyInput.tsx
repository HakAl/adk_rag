import { useState } from 'react';
import { Eye, EyeOff, ExternalLink, AlertCircle, CheckCircle, XCircle } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Card, CardContent } from './ui/card';
import { useApiKeys } from '../contexts/ApiKeyContext';
import { validateApiKey } from '../utils/apiKeyValidation';
import { Provider } from '../api/direct/coordinator';

interface ApiKeyInputProps {
  onComplete?: () => void;
}

export const ApiKeyInput = ({ onComplete }: ApiKeyInputProps) => {
  const { keys, setApiKeys, setProvider } = useApiKeys();

  const [anthropicKey, setAnthropicKey] = useState(keys.anthropic || '');
  const [googleKey, setGoogleKey] = useState(keys.google || '');
  const [selectedProvider, setSelectedProvider] = useState<Provider>('anthropic');
  const [showAnthropicKey, setShowAnthropicKey] = useState(false);
  const [showGoogleKey, setShowGoogleKey] = useState(false);
  const [anthropicError, setAnthropicError] = useState('');
  const [googleError, setGoogleError] = useState('');

  // Validate keys in real-time
  const validateKeys = () => {
    let hasError = false;

    // Only validate if user has entered something
    if (anthropicKey.trim()) {
      const validation = validateApiKey(anthropicKey, 'anthropic');
      if (!validation.valid) {
        setAnthropicError('Invalid key');
        hasError = true;
      } else {
        setAnthropicError('');
      }
    } else {
      setAnthropicError('');
    }

    if (googleKey.trim()) {
      const validation = validateApiKey(googleKey, 'google');
      if (!validation.valid) {
        setGoogleError('Invalid key');
        hasError = true;
      } else {
        setGoogleError('');
      }
    } else {
      setGoogleError('');
    }

    return !hasError;
  };

  const getKeyStatus = (key: string, error: string): 'empty' | 'valid' | 'invalid' => {
    if (!key.trim()) return 'empty';
    if (error) return 'invalid';
    return 'valid';
  };

  const anthropicStatus = getKeyStatus(anthropicKey, anthropicError);
  const googleStatus = getKeyStatus(googleKey, googleError);

  const hasAnthropicKey = anthropicKey.trim().length > 0 && !anthropicError;
  const hasGoogleKey = googleKey.trim().length > 0 && !googleError;
  const hasBothKeys = hasAnthropicKey && hasGoogleKey;
  const hasAtLeastOneKey = hasAnthropicKey || hasGoogleKey;

  const handleContinue = () => {
    if (!validateKeys()) {
      return;
    }

    if (!hasAtLeastOneKey) {
      return;
    }

    // Set keys in context
    setApiKeys({
      anthropic: anthropicKey.trim() || undefined,
      google: googleKey.trim() || undefined,
    });

    // Auto-detect provider based on which keys are set
    let providerToUse: Provider;
    if (hasBothKeys) {
      // Both keys set - use user's selection
      providerToUse = selectedProvider;
    } else if (hasGoogleKey) {
      // Only Google key set - use Google
      providerToUse = 'google';
    } else {
      // Only Anthropic key set - use Anthropic
      providerToUse = 'anthropic';
    }

    // Set provider in context
    setProvider(providerToUse);

    if (onComplete) {
      onComplete();
    }
  };

  const StatusIcon = ({ status }: { status: 'empty' | 'valid' | 'invalid' }) => {
    if (status === 'valid') {
      return <CheckCircle className="h-4 w-4 text-green-600 dark:text-green-400" />;
    }
    if (status === 'invalid') {
      return <XCircle className="h-4 w-4 text-red-600 dark:text-red-400" />;
    }
    return null;
  };

  const getBorderColor = (status: 'empty' | 'valid' | 'invalid') => {
    if (status === 'valid') return 'border-green-500/50';
    if (status === 'invalid') return 'border-red-500/50';
    return '';
  };

  return (
    <div className="p-4 space-y-4">
      {/* Warning Banner */}
      <Card className="glass-card border-yellow-500/50">
        <CardContent className="p-3 flex items-start gap-2">
          <AlertCircle className="h-4 w-4 text-yellow-500 flex-shrink-0 mt-0.5" />
          <div className="text-sm">
            <p className="font-medium text-yellow-600 dark:text-yellow-400">
              Keys stored in memory only
            </p>
            <p className="text-muted-foreground text-xs mt-1">
              Your API keys will be lost when you refresh the page or close your browser.
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Anthropic Section */}
      <Card className={`glass-card ${getBorderColor(anthropicStatus)}`}>
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm">Anthropic</h3>
              <StatusIcon status={anthropicStatus} />
            </div>
            <a
              href="https://console.anthropic.com/settings/keys"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline inline-flex items-center gap-1 text-xs"
            >
              Get key <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="anthropic-key" className="block text-xs text-muted-foreground">
                {anthropicStatus === 'empty' && 'Status: Not set'}
                {anthropicStatus === 'valid' && 'Status: Valid'}
                {anthropicStatus === 'invalid' && 'Status: Invalid'}
              </label>
            </div>
            <div className="relative">
              <Input
                id="anthropic-key"
                name={`api-key-anthropic-${Date.now()}`}
                type={showAnthropicKey ? 'text' : 'password'}
                value={anthropicKey}
                onChange={(e) => setAnthropicKey(e.target.value)}
                onFocus={(e) => e.target.removeAttribute('readonly')}
                onBlur={validateKeys}
                placeholder="sk-ant-..."
                className="glass-input pr-10"
                autoComplete="new-password"
                data-1p-ignore
                data-lpignore="true"
                readOnly
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => setShowAnthropicKey(!showAnthropicKey)}
                aria-label={showAnthropicKey ? 'Hide key' : 'Show key'}
              >
                {showAnthropicKey ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            {anthropicError && (
              <p className="text-xs text-red-500">{anthropicError}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Google Section */}
      <Card className={`glass-card ${getBorderColor(googleStatus)}`}>
        <CardContent className="p-4 space-y-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="font-semibold text-sm">Google</h3>
              <StatusIcon status={googleStatus} />
            </div>
            <a
              href="https://aistudio.google.com/app/apikey"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary hover:underline inline-flex items-center gap-1 text-xs"
            >
              Get key <ExternalLink className="h-3 w-3" />
            </a>
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <label htmlFor="google-key" className="block text-xs text-muted-foreground">
                {googleStatus === 'empty' && 'Status: Not set'}
                {googleStatus === 'valid' && 'Status: Valid'}
                {googleStatus === 'invalid' && 'Status: Invalid'}
              </label>
            </div>
            <div className="relative">
              <Input
                id="google-key"
                name={`api-key-google-${Date.now()}`}
                type={showGoogleKey ? 'text' : 'password'}
                value={googleKey}
                onChange={(e) => setGoogleKey(e.target.value)}
                onFocus={(e) => e.target.removeAttribute('readonly')}
                onBlur={validateKeys}
                placeholder="AIza..."
                className="glass-input pr-10"
                autoComplete="new-password"
                data-1p-ignore
                data-lpignore="true"
                readOnly
              />
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="absolute right-0 top-0 h-full px-3 hover:bg-transparent"
                onClick={() => setShowGoogleKey(!showGoogleKey)}
                aria-label={showGoogleKey ? 'Hide key' : 'Show key'}
              >
                {showGoogleKey ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </Button>
            </div>
            {googleError && (
              <p className="text-xs text-red-500">{googleError}</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Provider Selection (only show when both keys are valid) */}
      {hasBothKeys && (
        <div className="space-y-2">
          <label className="block text-sm font-medium">
            Default Provider
          </label>
          <div className="flex gap-4">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="provider"
                value="anthropic"
                checked={selectedProvider === 'anthropic'}
                onChange={(e) => setSelectedProvider(e.target.value as Provider)}
                className="w-4 h-4 text-primary focus:ring-2 focus:ring-primary"
              />
              <span className="text-sm">Anthropic</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="radio"
                name="provider"
                value="google"
                checked={selectedProvider === 'google'}
                onChange={(e) => setSelectedProvider(e.target.value as Provider)}
                className="w-4 h-4 text-primary focus:ring-2 focus:ring-primary"
              />
              <span className="text-sm">Google</span>
            </label>
          </div>
        </div>
      )}

      {/* Continue Button */}
      <Button
        onClick={handleContinue}
        disabled={!hasAtLeastOneKey}
        className="w-full glass-button"
      >
        Continue
      </Button>

      {/* Help Text */}
      <p className="text-xs text-muted-foreground text-center">
        At least one API key is required to use the chat.
      </p>
    </div>
  );
};
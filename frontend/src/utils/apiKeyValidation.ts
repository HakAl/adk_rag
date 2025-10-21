import { validateMessage, ValidationResult } from './messageValidation';

// API key specific constants
const MIN_KEY_LENGTH = 20;
const MAX_KEY_LENGTH = 200;

export type ApiKeyProvider = 'anthropic' | 'google';

/**
 * Validate API key format and content
 */
export const validateApiKey = (
  key: string,
  provider: ApiKeyProvider
): ValidationResult => {
  const trimmed = key.trim();

  // Reuse message validation for suspicious patterns and basic checks
  const baseValidation = validateMessage(trimmed);
  if (!baseValidation.valid) {
    return { valid: false, error: `API key ${baseValidation.error?.toLowerCase()}` };
  }

  // Length check specific to API keys
  if (trimmed.length < MIN_KEY_LENGTH) {
    return {
      valid: false,
      error: `API key is too short (minimum ${MIN_KEY_LENGTH} characters)`,
    };
  }

  if (trimmed.length > MAX_KEY_LENGTH) {
    return {
      valid: false,
      error: `API key is too long (maximum ${MAX_KEY_LENGTH} characters)`,
    };
  }

  // Provider-specific format validation
  if (provider === 'anthropic' && !trimmed.startsWith('sk-ant-')) {
    return {
      valid: false,
      error: 'Anthropic API keys must start with "sk-ant-"',
    };
  }

  if (provider === 'google' && !trimmed.startsWith('AIza')) {
    return {
      valid: false,
      error: 'Google API keys must start with "AIza"',
    };
  }

  return { valid: true };
};
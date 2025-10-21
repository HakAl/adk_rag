/**
 * Format API error messages for user-friendly display
 */
export const formatApiError = (errorMessage: string): string => {
  // Anthropic credit error
  if (errorMessage.includes('credit balance is too low')) {
    return 'Credit balance too low. Please add credits to your Anthropic account.';
  }

  // Anthropic API errors
  if (errorMessage.includes('Anthropic API error')) {
    // Try to extract the actual error message
    const match = errorMessage.match(/'message':\s*'([^']+)'/);
    if (match && match[1]) {
      return match[1];
    }
    return 'Anthropic API error. Please check your API key and try again.';
  }

  // Google API errors
  if (errorMessage.includes('Google API')) {
    if (errorMessage.includes('rate limit')) {
      return 'Google API rate limit exceeded. Please try again in a moment.';
    }
    return 'Google API error. Please check your API key and try again.';
  }

  // Rate limit errors
  if (errorMessage.includes('rate limit')) {
    return 'Rate limit exceeded. Please slow down and try again.';
  }

  // Session/auth errors
  if (errorMessage.includes('Session expired')) {
    return 'Session expired. Please refresh the page.';
  }

  if (errorMessage.includes('Security token invalid') || errorMessage.includes('CSRF')) {
    return 'Security token invalid. Please refresh the page.';
  }

  // API key errors
  if (errorMessage.includes('API key')) {
    return 'API key error. Please check your API key configuration.';
  }

  // Generic fallback - return first sentence or first 100 chars
  const firstSentence = errorMessage.split('.')[0];
  if (firstSentence.length <= 100) {
    return firstSentence + '.';
  }

  return errorMessage.substring(0, 100) + '...';
};
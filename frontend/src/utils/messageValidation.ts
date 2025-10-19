// Validation constants
export const MAX_MESSAGE_LENGTH = 16000;
export const MIN_MESSAGE_LENGTH = 1;
export const WARNING_THRESHOLD = 0.9;

// Simple client-side prompt injection detection patterns
const SUSPICIOUS_PATTERNS = [
  /ignore\s+(previous|prior|above|all)\s+(instructions?|prompts?|commands?)/i,
  /disregard\s+(previous|prior|above|all)/i,
  /forget\s+(everything|all|previous|instructions?)/i,
  /you\s+are\s+now\s+(a|an)/i,
  /system\s*:\s*/i,
  /<\|im_start\|>/i,
  /<\|im_end\|>/i,
  /\[INST\]/i,
  /\[\/INST\]/i,
  /override\s+your\s+(instructions?|programming)/i,
];

export interface ValidationResult {
  valid: boolean;
  error?: string;
}

/**
 * Check if message appears to be code/technical content
 */
export const isCodeContext = (message: string): boolean => {
  const codeIndicators = [
    'function', 'class', 'const', 'let', 'var', 'def', 'public', 'private',
    'import', 'require', 'return', 'if', 'else', 'for', 'while',
    '=>', 'async', 'await', '.map(', '.filter(', '.reduce(',
    'console.log', 'print(', 'System.out', 'fmt.Print'
  ];
  return codeIndicators.some(indicator => message.includes(indicator));
};

/**
 * Validate message on client side for immediate feedback
 */
export const validateMessage = (message: string): ValidationResult => {
  const trimmed = message.trim();

  if (trimmed.length < MIN_MESSAGE_LENGTH) {
    return { valid: false, error: 'Message cannot be empty' };
  }

  if (trimmed.length > MAX_MESSAGE_LENGTH) {
    return {
      valid: false,
      error: `Message is too long (${trimmed.length}/${MAX_MESSAGE_LENGTH} characters)`
    };
  }

  // Check for null bytes
  if (trimmed.includes('\x00')) {
    return { valid: false, error: 'Message contains invalid characters' };
  }

  // Check for suspicious patterns - skip if code context detected
  if (!isCodeContext(trimmed)) {
    for (const pattern of SUSPICIOUS_PATTERNS) {
      if (pattern.test(trimmed)) {
        return {
          valid: false,
          error: 'Message contains suspicious content. Please rephrase your query.'
        };
      }
    }
  }

  return { valid: true };
};
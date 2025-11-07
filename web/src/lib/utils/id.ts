/**
 * ID Generation Utilities
 * Cryptographically secure ID generation functions
 */

// ============================================================================
// Generic ID Generator
// ============================================================================

/**
 * Generate a unique ID with custom prefix
 * Uses crypto.randomUUID() for cryptographically secure random values
 *
 * @param prefix - Prefix for the ID (alphanumeric only, e.g., 'credit', 'adj', 'usage')
 * @returns Unique ID in format: `${prefix}-${uuid}`
 * @throws {Error} If prefix is empty, whitespace-only, or contains non-alphanumeric characters
 *
 * @example
 * generateId('credit') // 'credit-a1b2c3d4-...'
 * generateId('') // throws Error: empty
 * generateId('my-id') // throws Error: contains hyphen
 * generateId('test ID') // throws Error: contains space
 */
export function generateId(prefix: string): string {
  const trimmedPrefix = prefix.trim()

  // Check for empty prefix
  if (!trimmedPrefix) {
    throw new Error('Prefix cannot be empty')
  }

  // Validate format: alphanumeric only (a-z, A-Z, 0-9)
  if (!/^[a-z0-9]+$/i.test(trimmedPrefix)) {
    throw new Error('Prefix must contain only alphanumeric characters (a-z, 0-9)')
  }

  return `${trimmedPrefix}-${crypto.randomUUID()}`
}
// ============================================================================
// Specialized ID Generators
// ============================================================================

/**
 * Generate a unique credit ID
 * @returns Credit ID in format: 'credit-{uuid}'
 */
export function generateCreditId(): string {
  return generateId('credit')
}

/**
 * Generate a unique adjustment ID
 * @returns Adjustment ID in format: 'adj-{uuid}'
 */
export function generateAdjustmentId(): string {
  return generateId('adj')
}

/**
 * Generate a unique usage ID
 * @returns Usage ID in format: 'usage-{uuid}'
 */
export function generateUsageId(): string {
  return generateId('usage')
}

/**
 * Generate a unique resource ID
 * @returns Resource ID in format: 'resource-{uuid}'
 */
export function generateResourceId(): string {
  return generateId('resource')
}

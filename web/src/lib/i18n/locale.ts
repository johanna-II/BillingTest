/**
 * Internationalization (i18n) Support
 * Simple locale management - ready for full i18n library integration
 */

// ============================================================================
// Supported Locales
// ============================================================================

export type SupportedLocale = 'ko' | 'en'

/**
 * Default locale for the application
 * Can be overridden by user preference or browser settings
 */
export const DEFAULT_LOCALE: SupportedLocale = 'ko'

/**
 * Get current locale
 * Automatically detects browser language and falls back to default
 * Supports ko (Korean) and en (English)
 *
 * Note: Can be extended with next-intl or react-i18next for advanced i18n features
 *
 * @returns Current locale code
 */
export function getCurrentLocale(): SupportedLocale {
  // Check browser language if available (SSR-safe)
  if (globalThis.window !== undefined && globalThis.navigator) {
    const browserLang = globalThis.navigator.language.toLowerCase()

    // Match browser language to supported locales
    if (browserLang.startsWith('ko')) {
      return 'ko'
    }
    if (browserLang.startsWith('en')) {
      return 'en'
    }
  }

  // Fallback to default locale
  return DEFAULT_LOCALE
}

/**
 * Format currency with locale
 * @param amount - Amount to format
 * @param locale - Locale code
 * @returns Formatted currency string
 */
export function formatCurrencyWithLocale(
  amount: number,
  locale: SupportedLocale = DEFAULT_LOCALE
): string {
  const localeMap: Record<SupportedLocale, string> = {
    ko: 'ko-KR',
    en: 'en-US',
  }

  return new Intl.NumberFormat(localeMap[locale], {
    style: 'currency',
    currency: 'KRW',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount)
}

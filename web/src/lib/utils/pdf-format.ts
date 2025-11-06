/**
 * PDF Formatting Utilities
 * Pure functions for formatting values in PDF documents
 */

import type { Currency } from '@/types/billing'
import { PDF_CONFIG } from '@/constants/pdf'

// ============================================================================
// Locale Helpers
// ============================================================================

/**
 * Get appropriate locale for a given currency
 * @param currency - Currency code
 * @returns Locale string (e.g., 'ko-KR', 'en-US')
 */
export function getLocaleForCurrency(currency: Currency): string {
  return PDF_CONFIG.FORMAT.LOCALE_MAP[currency as keyof typeof PDF_CONFIG.FORMAT.LOCALE_MAP]
    ?? PDF_CONFIG.FORMAT.DEFAULT_LOCALE
}

// ============================================================================
// Number Formatting
// ============================================================================

/**
 * Format a number with locale-specific formatting
 * @param value - Number to format
 * @param currency - Currency for locale determination
 * @returns Formatted number string
 */
export function formatNumber(value: number | undefined, currency: Currency): string {
  const locale = getLocaleForCurrency(currency)
  return value?.toLocaleString(locale) ?? String(PDF_CONFIG.DEFAULT.ZERO)
}

/**
 * Format a currency value with symbol and locale
 * @param value - Amount to format
 * @param currency - Currency code
 * @returns Formatted currency string (e.g., '₩1,000', '$10.00')
 */
export function formatCurrency(value: number, currency: Currency): string {
  const locale = getLocaleForCurrency(currency)

  try {
    // Check if this currency has a specific fraction digit override
    const fractionDigits = PDF_CONFIG.FORMAT.FRACTION_DIGITS[
      currency as keyof typeof PDF_CONFIG.FORMAT.FRACTION_DIGITS
    ]

    // Build formatter options
    const options: Intl.NumberFormatOptions = {
      style: 'currency',
      currency: currency,
    }

    // Only override fraction digits if explicitly configured
    // Otherwise, let Intl.NumberFormat use currency-appropriate defaults
    if (fractionDigits !== undefined) {
      options.minimumFractionDigits = fractionDigits
      options.maximumFractionDigits = fractionDigits
    }

    return new Intl.NumberFormat(locale, options).format(value)
  } catch {
    // Fallback if currency code is not supported
    return `${value.toLocaleString(locale)} ${currency}`
  }
}

/**
 * Format adjustment amount with sign
 * @param type - Adjustment type (DISCOUNT or SURCHARGE)
 * @param amount - Adjustment amount
 * @param currency - Currency code
 * @returns Formatted adjustment string with sign (e.g., '-₩5,000', '+₩2,000')
 */
export function formatAdjustmentAmount(
  type: string | undefined,
  amount: number | undefined,
  currency: Currency
): string {
  const sign = type === 'SURCHARGE' ? '+' : '-'
  const absAmount = Math.abs(amount ?? PDF_CONFIG.DEFAULT.ZERO)
  return `${sign}${formatCurrency(absAmount, currency)}`
}

// ============================================================================
// File Name Generation
// ============================================================================

/**
 * Generate PDF file name from billing month
 * @param month - Billing month (e.g., '2024-11')
 * @returns File name for download
 */
export function generatePDFFileName(month: string | undefined): string {
  const monthStr = month ?? PDF_CONFIG.DEFAULT.MONTH
  return `billing-statement-${monthStr}.pdf`
}

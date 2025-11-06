/**
 * PDF Configuration Constants
 * Centralized PDF generation configuration
 */

import type { Currency } from '@/types/billing'

// ============================================================================
// PDF Configuration Shape
// ============================================================================

/**
 * PDF Configuration Shape
 * Validates structure while allowing literal type inference
 */
type PDFConfigShape = {
  readonly PAGE: {
    readonly MARGIN_LEFT: number
    readonly MARGIN_TOP: number
    readonly MARGIN_BOTTOM: number
  }
  readonly FONT_SIZE: {
    readonly TITLE: number
    readonly SECTION: number
    readonly BODY: number
  }
  readonly SPACING: {
    readonly AFTER_TITLE: number
    readonly LINE_HEIGHT: number
    readonly SECTION_GAP: number
    readonly SECTION_HEADER_GAP: number
    readonly BEFORE_SUMMARY: number
    readonly SUMMARY_HEADER: number
    readonly FINAL_AMOUNT_GAP: number
  }
  readonly TABLE: {
    readonly START_Y_OFFSET: number
  }
  readonly FONT: {
    readonly FAMILY: string
    readonly STYLE_NORMAL: string
    readonly STYLE_BOLD: string
  }
  readonly LABELS: {
    readonly [key: string]: string
  }
  readonly TABLE_HEADERS: {
    readonly LINE_ITEMS: readonly string[]
    readonly ADJUSTMENTS: readonly string[]
    readonly CREDITS: readonly string[]
  }
  readonly DEFAULT: {
    readonly CURRENCY: Currency
    readonly MONTH: string
    readonly ZERO: number
  }
  readonly FORMAT: {
    readonly LOCALE_MAP: {
      readonly [key: string]: string
    }
    readonly DEFAULT_LOCALE: string
    readonly FRACTION_DIGITS: {
      readonly [key: string]: number
    }
  }
}

// ============================================================================
// PDF Configuration
// ============================================================================

/**
 * PDF Configuration
 * Uses 'as const satisfies' for literal types with shape validation
 */
export const PDF_CONFIG = {
  PAGE: {
    MARGIN_LEFT: 20,
    MARGIN_TOP: 20,
    MARGIN_BOTTOM: 20,
  },
  FONT_SIZE: {
    TITLE: 20,
    SECTION: 14,
    BODY: 12,
  },
  SPACING: {
    AFTER_TITLE: 15,
    LINE_HEIGHT: 7,
    SECTION_GAP: 10,
    SECTION_HEADER_GAP: 3,
    BEFORE_SUMMARY: 15,
    SUMMARY_HEADER: 10,
    FINAL_AMOUNT_GAP: 5,
  },
  TABLE: {
    START_Y_OFFSET: 50,
  },
  FONT: {
    FAMILY: 'helvetica',
    STYLE_NORMAL: 'normal',
    STYLE_BOLD: 'bold',
  },
  LABELS: {
    TITLE: 'Billing Statement',
    MONTH: 'Month',
    CURRENCY: 'Currency',
    ADJUSTMENTS_TITLE: 'Adjustments (Discounts/Surcharges)',
    CREDITS_TITLE: 'Applied Credits',
    SUMMARY_TITLE: 'Summary',
    SUBTOTAL: 'Subtotal',
    BILLING_GROUP_DISCOUNT: 'Billing Group Discount',
    ADJUSTMENTS_TOTAL: 'Adjustments Total',
    CREDIT_APPLIED: 'Credit Applied',
    CHARGE_BEFORE_VAT: 'Charge (before VAT)',
    VAT: 'VAT (10%)',
    UNPAID_AMOUNT_PREVIOUS: 'Unpaid Amount (Previous)',
    LATE_FEE: 'Late Fee',
    TOTAL_AMOUNT: 'Total Amount',
    NOT_AVAILABLE: 'N/A',
    NO_CAMPAIGN: '-',
  },
  TABLE_HEADERS: {
    LINE_ITEMS: ['Resource', 'Quantity', 'Unit Price', 'Amount'],
    ADJUSTMENTS: ['Type', 'Description', 'Level', 'Amount'],
    CREDITS: ['Type', 'Amount Applied', 'Remaining Balance', 'Campaign'],
  },
  DEFAULT: {
    CURRENCY: 'KRW' as Currency,
    MONTH: 'unknown',
    ZERO: 0,
  },
  FORMAT: {
    LOCALE_MAP: {
      KRW: 'ko-KR',
      USD: 'en-US',
      EUR: 'en-GB',
      JPY: 'ja-JP',
    },
    DEFAULT_LOCALE: 'en-US',
    FRACTION_DIGITS: {
      KRW: 0,
      JPY: 0,
    },
  },
} as const satisfies PDFConfigShape

/**
 * Derive type from constant for perfect type safety
 */
export type PDFConfigType = typeof PDF_CONFIG

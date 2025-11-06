/**
 * Statement PDF Generator
 * Type-safe PDF generation with configurable layouts
 */

import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import type { BillingStatement, Currency } from '@/types/billing'

// ============================================================================
// Configuration
// ============================================================================

const PDF_CONFIG = {
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
    SECTION_HEADER_GAP: 3, // Gap after section titles before tables
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
    } as const,
    DEFAULT_LOCALE: 'en-US',
    // Currency-specific fraction digit overrides
    // Only override when the default behavior needs adjustment
    FRACTION_DIGITS: {
      KRW: 0, // Korean Won doesn't use decimal places
      JPY: 0, // Japanese Yen doesn't use decimal places
      // USD, EUR, GBP, etc. use default (2 decimal places)
    } as const,
  },
} as const

// ============================================================================
// Type Definitions
// ============================================================================

type PDFDocument = jsPDF & {
  lastAutoTable?: {
    finalY: number
  }
}

// ============================================================================
// PDF Generator
// ============================================================================

export function generateStatementPDF(statement: BillingStatement): void {
  const doc: PDFDocument = new jsPDF()
  let currentY: number = PDF_CONFIG.PAGE.MARGIN_TOP

  // Render sections
  currentY = renderHeader(doc, statement, currentY)
  currentY = renderLineItemsTable(doc, statement, currentY)
  currentY = renderAdjustmentsTable(doc, statement, currentY)
  currentY = renderCreditsTable(doc, statement, currentY)
  renderSummary(doc, statement, currentY)

  // Download PDF
  const fileName = generateFileName(statement.month)
  doc.save(fileName)
}

// ============================================================================
// Section Renderers
// ============================================================================

function renderHeader(doc: PDFDocument, statement: BillingStatement, startY: number): number {
  const currency = statement.currency ?? PDF_CONFIG.DEFAULT.CURRENCY

  // Title
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.TITLE)
  doc.text(PDF_CONFIG.LABELS.TITLE, PDF_CONFIG.PAGE.MARGIN_LEFT, startY)
  startY += PDF_CONFIG.SPACING.AFTER_TITLE

  // Basic Info
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.BODY)
  doc.text(
    `${PDF_CONFIG.LABELS.MONTH}: ${statement.month ?? PDF_CONFIG.LABELS.NOT_AVAILABLE}`,
    PDF_CONFIG.PAGE.MARGIN_LEFT,
    startY
  )
  startY += PDF_CONFIG.SPACING.LINE_HEIGHT

  doc.text(
    `${PDF_CONFIG.LABELS.CURRENCY}: ${currency}`,
    PDF_CONFIG.PAGE.MARGIN_LEFT,
    startY
  )
  startY += PDF_CONFIG.SPACING.LINE_HEIGHT

  return startY
}

function renderLineItemsTable(
  doc: PDFDocument,
  statement: BillingStatement,
  startY: number
): number {
  if (!statement.lineItems || statement.lineItems.length === 0) {
    return startY
  }

  const currency = statement.currency ?? PDF_CONFIG.DEFAULT.CURRENCY

  autoTable(doc, {
    startY,
    head: [[...PDF_CONFIG.TABLE_HEADERS.LINE_ITEMS]],
    body: statement.lineItems.map((item) => [
      item.counterName ?? item.resourceName ?? PDF_CONFIG.LABELS.NOT_AVAILABLE,
      formatNumber(item.quantity, currency), // Non-monetary: quantity
      formatCurrency(item.unitPrice, currency), // Monetary: unit price
      formatCurrency(item.amount, currency), // Monetary: total amount
    ]),
  })

  return getTableEndPosition(doc, startY)
}

function renderAdjustmentsTable(
  doc: PDFDocument,
  statement: BillingStatement,
  startY: number
): number {
  if (!statement.appliedAdjustments || statement.appliedAdjustments.length === 0) {
    return startY
  }

  const currency = statement.currency ?? PDF_CONFIG.DEFAULT.CURRENCY

  // Section title
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.SECTION)
  doc.text(PDF_CONFIG.LABELS.ADJUSTMENTS_TITLE, PDF_CONFIG.PAGE.MARGIN_LEFT, startY)
  startY += PDF_CONFIG.SPACING.SECTION_HEADER_GAP

  autoTable(doc, {
    startY,
    head: [[...PDF_CONFIG.TABLE_HEADERS.ADJUSTMENTS]],
    body: statement.appliedAdjustments.map((adj) => [
      adj.type ?? PDF_CONFIG.LABELS.NOT_AVAILABLE,
      adj.description ?? PDF_CONFIG.LABELS.NOT_AVAILABLE,
      adj.level ?? PDF_CONFIG.LABELS.NOT_AVAILABLE,
      formatAdjustmentAmount(adj.type, adj.amount, currency),
    ]),
  })

  return getTableEndPosition(doc, startY)
}

function renderCreditsTable(
  doc: PDFDocument,
  statement: BillingStatement,
  startY: number
): number {
  if (!statement.appliedCredits || statement.appliedCredits.length === 0) {
    return startY
  }

  const currency = statement.currency ?? PDF_CONFIG.DEFAULT.CURRENCY

  // Section title
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.SECTION)
  doc.text(PDF_CONFIG.LABELS.CREDITS_TITLE, PDF_CONFIG.PAGE.MARGIN_LEFT, startY)
  startY += PDF_CONFIG.SPACING.SECTION_HEADER_GAP

  autoTable(doc, {
    startY,
    head: [[...PDF_CONFIG.TABLE_HEADERS.CREDITS]],
    body: statement.appliedCredits.map((credit) => [
      credit.type ?? PDF_CONFIG.LABELS.NOT_AVAILABLE,
      formatCurrency(credit.amountApplied, currency), // Monetary: amount applied
      formatCurrency(credit.remainingBalance, currency), // Monetary: remaining balance
      credit.campaignName ?? credit.campaignId ?? PDF_CONFIG.LABELS.NO_CAMPAIGN,
    ]),
  })

  return getTableEndPosition(doc, startY)
}

function renderSummary(doc: PDFDocument, statement: BillingStatement, startY: number): void {
  const currency = statement.currency ?? PDF_CONFIG.DEFAULT.CURRENCY
  let summaryY = startY + PDF_CONFIG.SPACING.BEFORE_SUMMARY

  // Check if we need a new page for the summary
  // Estimate ~15 lines for complete summary section
  const estimatedSummaryHeight = 15 * PDF_CONFIG.SPACING.LINE_HEIGHT
  const pageHeight = doc.internal.pageSize.height

  if (summaryY + estimatedSummaryHeight > pageHeight - PDF_CONFIG.PAGE.MARGIN_BOTTOM) {
    doc.addPage()
    summaryY = PDF_CONFIG.PAGE.MARGIN_TOP
  }

  // Summary Title
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.SECTION)
  doc.text(PDF_CONFIG.LABELS.SUMMARY_TITLE, PDF_CONFIG.PAGE.MARGIN_LEFT, summaryY)
  summaryY += PDF_CONFIG.SPACING.SUMMARY_HEADER

  // Summary Items
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.BODY)
  doc.setFont(PDF_CONFIG.FONT.FAMILY, PDF_CONFIG.FONT.STYLE_NORMAL)

  summaryY = renderSummaryLine(doc, PDF_CONFIG.LABELS.SUBTOTAL, statement.subtotal, currency, summaryY)

  if (shouldRenderValue(statement.billingGroupDiscount)) {
    summaryY = renderSummaryLine(
      doc,
      PDF_CONFIG.LABELS.BILLING_GROUP_DISCOUNT,
      -statement.billingGroupDiscount,
      currency,
      summaryY
    )
  }

  if (shouldRenderValue(statement.adjustmentTotal)) {
    summaryY = renderSummaryLine(
      doc,
      PDF_CONFIG.LABELS.ADJUSTMENTS_TOTAL,
      statement.adjustmentTotal,
      currency,
      summaryY,
      true
    )
  }

  if (shouldRenderValue(statement.creditApplied)) {
    summaryY = renderSummaryLine(
      doc,
      PDF_CONFIG.LABELS.CREDIT_APPLIED,
      -statement.creditApplied,
      currency,
      summaryY
    )
  }

  if (shouldRenderValue(statement.charge)) {
    summaryY = renderSummaryLine(
      doc,
      PDF_CONFIG.LABELS.CHARGE_BEFORE_VAT,
      statement.charge,
      currency,
      summaryY
    )
  }

  if (shouldRenderValue(statement.vat)) {
    summaryY = renderSummaryLine(doc, PDF_CONFIG.LABELS.VAT, statement.vat, currency, summaryY)
  }

  if (shouldRenderValue(statement.unpaidAmount)) {
    summaryY = renderSummaryLine(
      doc,
      PDF_CONFIG.LABELS.UNPAID_AMOUNT_PREVIOUS,
      statement.unpaidAmount,
      currency,
      summaryY
    )
  }

  if (shouldRenderValue(statement.lateFee)) {
    summaryY = renderSummaryLine(
      doc,
      PDF_CONFIG.LABELS.LATE_FEE,
      statement.lateFee,
      currency,
      summaryY
    )
  }

  // Total Amount (bold)
  summaryY += PDF_CONFIG.SPACING.FINAL_AMOUNT_GAP
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.SECTION)
  doc.setFont(PDF_CONFIG.FONT.FAMILY, PDF_CONFIG.FONT.STYLE_BOLD)
  const totalAmount = statement.totalAmount ?? statement.amount ?? PDF_CONFIG.DEFAULT.ZERO
  doc.text(
    `${PDF_CONFIG.LABELS.TOTAL_AMOUNT}: ${formatCurrency(totalAmount, currency)}`,
    PDF_CONFIG.PAGE.MARGIN_LEFT,
    summaryY
  )
}

// ============================================================================
// Helper Functions
// ============================================================================

function getLocaleForCurrency(currency: Currency): string {
  return PDF_CONFIG.FORMAT.LOCALE_MAP[currency as keyof typeof PDF_CONFIG.FORMAT.LOCALE_MAP]
    ?? PDF_CONFIG.FORMAT.DEFAULT_LOCALE
}

function renderSummaryLine(
  doc: PDFDocument,
  label: string,
  value: number,
  currency: Currency,
  y: number,
  showSign: boolean = false
): number {
  let sign = ''
  if (showSign) {
    sign = value >= 0 ? '+' : '-'
  }
  const absValue = showSign ? Math.abs(value) : value
  doc.text(
    `${label}: ${sign}${formatCurrency(absValue, currency)}`,
    PDF_CONFIG.PAGE.MARGIN_LEFT,
    y
  )
  return y + PDF_CONFIG.SPACING.LINE_HEIGHT
}
function getTableEndPosition(doc: PDFDocument, fallbackY: number): number {
  return (doc.lastAutoTable?.finalY ?? fallbackY) + PDF_CONFIG.SPACING.SECTION_GAP
}

function formatNumber(value: number | undefined, currency: Currency): string {
  const locale = getLocaleForCurrency(currency)
  return value?.toLocaleString(locale) ?? String(PDF_CONFIG.DEFAULT.ZERO)
}

function formatCurrency(value: number, currency: Currency): string {
  const locale = getLocaleForCurrency(currency)

  // Use Intl.NumberFormat for proper currency formatting
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

function formatAdjustmentAmount(
  type: string | undefined,
  amount: number | undefined,
  currency: Currency
): string {
  const sign = type === 'SURCHARGE' ? '+' : '-'
  const absAmount = Math.abs(amount ?? PDF_CONFIG.DEFAULT.ZERO)
  return `${sign}${formatCurrency(absAmount, currency)}`
}

function shouldRenderValue(value: number | undefined): value is number {
  // Render all defined numeric values, including zero
  // This ensures transparency (e.g., "Discount: 0.00 KRW" confirms no discount)
  return value !== undefined && value !== null
}

function generateFileName(month: string | undefined): string {
  const monthStr = month ?? PDF_CONFIG.DEFAULT.MONTH
  return `billing-statement-${monthStr}.pdf`
}

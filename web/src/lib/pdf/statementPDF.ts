/**
 * Statement PDF Generator
 * Type-safe PDF generation with configurable layouts
 */

import jsPDF from 'jspdf'
import autoTable from 'jspdf-autotable'
import type { BillingStatement, Currency } from '@/types/billing'
import { PDF_CONFIG, getVATLabel } from '@/constants/pdf'
import {
  formatNumber,
  formatCurrency,
  formatAdjustmentAmount,
  generatePDFFileName,
} from '@/lib/utils/pdf-format'

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
  const fileName = generatePDFFileName(statement.month)
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
      formatNumber(item.quantity, currency),
      formatCurrency(item.unitPrice, currency),
      formatCurrency(item.amount, currency),
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
      formatCurrency(credit.amountApplied, currency),
      formatCurrency(credit.remainingBalance, currency),
      credit.campaignName ?? credit.campaignId ?? PDF_CONFIG.LABELS.NO_CAMPAIGN,
    ]),
  })

  return getTableEndPosition(doc, startY)
}

function renderSummary(doc: PDFDocument, statement: BillingStatement, startY: number): void {
  const currency = statement.currency ?? PDF_CONFIG.DEFAULT.CURRENCY
  let summaryY = startY + PDF_CONFIG.SPACING.BEFORE_SUMMARY

  // Check if we need a new page for the summary
  const estimatedSummaryHeight = calculateSummaryHeight(statement)
  const pageHeight = doc.internal.pageSize.height

  if (summaryY + estimatedSummaryHeight > pageHeight - PDF_CONFIG.PAGE.MARGIN_BOTTOM) {
    doc.addPage()
    summaryY = PDF_CONFIG.PAGE.MARGIN_TOP
  }

  // Render summary content
  summaryY = renderSummaryHeader(doc, summaryY)
  summaryY = renderSummaryItems(doc, statement, currency, summaryY)
  renderSummaryTotal(doc, statement, currency, summaryY)
}

function calculateSummaryHeight(statement: BillingStatement): number {
  // Count lines: Title + Total (always present) + optional items
  const optionalValues = [
    statement.subtotal,
    statement.billingGroupDiscount,
    statement.adjustmentTotal,
    statement.creditApplied,
    statement.charge,
    statement.vat,
    statement.unpaidAmount,
    statement.lateFee,
  ]

  const visibleItemCount = optionalValues.filter(shouldRenderValue).length
  const totalLines = 2 + visibleItemCount // Title + Total + visible items

  return (
    totalLines * PDF_CONFIG.SPACING.LINE_HEIGHT +
    PDF_CONFIG.SPACING.SUMMARY_HEADER +
    PDF_CONFIG.SPACING.FINAL_AMOUNT_GAP
  )
}

function renderSummaryHeader(doc: PDFDocument, y: number): number {
  doc.setFontSize(PDF_CONFIG.FONT_SIZE.SECTION)
  doc.text(PDF_CONFIG.LABELS.SUMMARY_TITLE, PDF_CONFIG.PAGE.MARGIN_LEFT, y)
  return y + PDF_CONFIG.SPACING.SUMMARY_HEADER
}

/**
 * Summary item configuration for data-driven rendering
 */
type SummaryItemConfig = {
  readonly value: number | undefined
  readonly label: string
  readonly negate?: boolean
  readonly showSign?: boolean
}

function renderSummaryItems(
  doc: PDFDocument,
  statement: BillingStatement,
  currency: Currency,
  startY: number
): number {
  let y = startY

  doc.setFontSize(PDF_CONFIG.FONT_SIZE.BODY)
  doc.setFont(PDF_CONFIG.FONT.FAMILY, PDF_CONFIG.FONT.STYLE_NORMAL)

  // Subtotal (always shown)
  y = renderSummaryLine(doc, PDF_CONFIG.LABELS.SUBTOTAL, statement.subtotal, currency, y)

  // Optional items - data-driven approach for maintainability
  const optionalItems: readonly SummaryItemConfig[] = [
    {
      value: statement.billingGroupDiscount,
      label: PDF_CONFIG.LABELS.BILLING_GROUP_DISCOUNT,
      negate: true,
    },
    {
      value: statement.adjustmentTotal,
      label: PDF_CONFIG.LABELS.ADJUSTMENTS_TOTAL,
      showSign: true,
    },
    {
      value: statement.creditApplied,
      label: PDF_CONFIG.LABELS.CREDIT_APPLIED,
      negate: true,
    },
    {
      value: statement.charge,
      label: PDF_CONFIG.LABELS.CHARGE_BEFORE_VAT,
    },
    {
      value: statement.vat,
      label: getVATLabel(),
    },
    {
      value: statement.unpaidAmount,
      label: PDF_CONFIG.LABELS.UNPAID_AMOUNT_PREVIOUS,
    },
    {
      value: statement.lateFee,
      label: PDF_CONFIG.LABELS.LATE_FEE,
    },
  ]

  // Render each optional item
  for (const item of optionalItems) {
    if (shouldRenderValue(item.value)) {
      const displayValue = item.negate ? -item.value : item.value
      y = renderSummaryLine(doc, item.label, displayValue, currency, y, item.showSign)
    }
  }

  return y
}

function renderSummaryTotal(
  doc: PDFDocument,
  statement: BillingStatement,
  currency: Currency,
  y: number
): void {
  const summaryY = y + PDF_CONFIG.SPACING.FINAL_AMOUNT_GAP
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

function shouldRenderValue(value: number | undefined): value is number {
  // Render all defined numeric values, including zero
  // This ensures transparency (e.g., "Discount: 0.00 KRW" confirms no discount)
  return value !== undefined && value !== null
}

import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import type { BillingStatement } from '@/types/billing';

export function generateStatementPDF(statement: BillingStatement): void {
  const doc = new jsPDF();

  // Title
  doc.setFontSize(20);
  doc.text('Billing Statement', 20, 20);
  
  // Basic Info
  doc.setFontSize(12);
  doc.text(`Month: ${statement.month || 'N/A'}`, 20, 35);
  doc.text(`Currency: ${statement.currency || 'KRW'}`, 20, 42);
  
  // Line Items Table
  let currentY = 50;
  
  if (statement.lineItems && statement.lineItems.length > 0) {
    autoTable(doc, {
      startY: currentY,
      head: [['Resource', 'Quantity', 'Unit Price', 'Amount']],
      body: statement.lineItems.map(item => [
        item.counterName || item.resourceName || 'N/A',
        item.quantity?.toString() || '0',
        item.unitPrice?.toLocaleString() || '0',
        item.amount?.toLocaleString() || '0',
      ]),
    });
    currentY = (doc as any).lastAutoTable?.finalY + 10 || currentY + 10;
  }
  
  // Applied Adjustments Table (Discounts/Surcharges)
  if (statement.appliedAdjustments && statement.appliedAdjustments.length > 0) {
    doc.setFontSize(14);
    doc.text('Adjustments (Discounts/Surcharges)', 20, currentY);
    currentY += 5;
    
    autoTable(doc, {
      startY: currentY,
      head: [['Type', 'Description', 'Level', 'Amount']],
      body: statement.appliedAdjustments.map(adj => [
        adj.type || 'N/A',
        adj.description || 'N/A',
        adj.level || 'N/A',
        `${adj.type === 'SURCHARGE' ? '+' : '-'}${Math.abs(adj.amount || 0).toLocaleString()} ${statement.currency || 'KRW'}`,
      ]),
    });
    currentY = (doc as any).lastAutoTable?.finalY + 10 || currentY + 10;
  }
  
  // Applied Credits Table
  if (statement.appliedCredits && statement.appliedCredits.length > 0) {
    doc.setFontSize(14);
    doc.text('Applied Credits', 20, currentY);
    currentY += 5;
    
    autoTable(doc, {
      startY: currentY,
      head: [['Type', 'Amount Applied', 'Remaining Balance', 'Campaign']],
      body: statement.appliedCredits.map(credit => [
        credit.type || 'N/A',
        credit.amountApplied?.toLocaleString() || '0',
        credit.remainingBalance?.toLocaleString() || '0',
        credit.campaignName || credit.campaignId || '-',
      ]),
    });
    currentY = (doc as any).lastAutoTable?.finalY + 10 || currentY + 10;
  }
  
  // Summary
  const finalY = currentY;
  
  doc.setFontSize(14);
  doc.text('Summary', 20, finalY + 15);
  
  doc.setFontSize(12);
  let summaryY = finalY + 25;
  const currency = statement.currency || 'KRW';
  
  doc.text(`Subtotal: ${statement.subtotal?.toLocaleString() || '0'} ${currency}`, 20, summaryY);
  summaryY += 7;
  
  // Show billing group discount if present
  if (statement.billingGroupDiscount && statement.billingGroupDiscount > 0) {
    doc.text(`Billing Group Discount: -${statement.billingGroupDiscount.toLocaleString()} ${currency}`, 20, summaryY);
    summaryY += 7;
  }
  
  // Show total adjustments (discounts/surcharges)
  if (statement.adjustmentTotal) {
    const sign = statement.adjustmentTotal >= 0 ? '+' : '-';
    doc.text(`Adjustments Total: ${sign}${Math.abs(statement.adjustmentTotal).toLocaleString()} ${currency}`, 20, summaryY);
    summaryY += 7;
  }
  
  // Show total credits applied
  if (statement.creditApplied && statement.creditApplied > 0) {
    doc.text(`Credit Applied: -${statement.creditApplied.toLocaleString()} ${currency}`, 20, summaryY);
    summaryY += 7;
  }
  
  // Show charge amount before VAT if available
  if (statement.charge !== undefined && statement.charge !== null) {
    doc.text(`Charge (before VAT): ${statement.charge.toLocaleString()} ${currency}`, 20, summaryY);
    summaryY += 7;
  }
  
  // VAT
  if (statement.vat !== undefined && statement.vat !== null) {
    doc.text(`VAT (10%): ${statement.vat.toLocaleString()} ${currency}`, 20, summaryY);
    summaryY += 7;
  }
  
  // Show unpaid amount from previous period
  if (statement.unpaidAmount && statement.unpaidAmount > 0) {
    doc.text(`Unpaid Amount (Previous): ${statement.unpaidAmount.toLocaleString()} ${currency}`, 20, summaryY);
    summaryY += 7;
  }
  
  // Show late fee if applicable
  if (statement.lateFee && statement.lateFee > 0) {
    doc.text(`Late Fee: ${statement.lateFee.toLocaleString()} ${currency}`, 20, summaryY);
    summaryY += 7;
  }
  
  summaryY += 5;
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  const totalAmount = statement.totalAmount || statement.amount || 0;
  doc.text(`Total Amount: ${totalAmount.toLocaleString()} ${currency}`, 20, summaryY);
  
  // Download
  const fileName = `billing-statement-${statement.month || 'unknown'}.pdf`;
  doc.save(fileName);
}

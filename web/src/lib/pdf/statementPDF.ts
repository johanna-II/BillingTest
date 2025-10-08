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
  if (statement.lineItems && statement.lineItems.length > 0) {
    autoTable(doc, {
      startY: 50,
      head: [['Resource', 'Quantity', 'Unit Price', 'Amount']],
      body: statement.lineItems.map(item => [
        item.counterName || item.resourceName || 'N/A',
        item.quantity?.toString() || '0',
        item.unitPrice?.toLocaleString() || '0',
        item.amount?.toLocaleString() || '0',
      ]),
    });
  }
  
  // Summary
  const finalY = (doc as any).lastAutoTable?.finalY || 50;
  
  doc.setFontSize(14);
  doc.text('Summary', 20, finalY + 15);
  
  doc.setFontSize(12);
  doc.text(`Subtotal: ${statement.subtotal?.toLocaleString() || '0'} KRW`, 20, finalY + 25);
  
  if (statement.billingGroupDiscount) {
    doc.text(`Discount: -${statement.billingGroupDiscount.toLocaleString()} KRW`, 20, finalY + 32);
  }
  
  if (statement.creditApplied) {
    doc.text(`Credit Applied: -${statement.creditApplied.toLocaleString()} KRW`, 20, finalY + 39);
  }
  
  doc.text(`VAT (10%): ${statement.vat?.toLocaleString() || '0'} KRW`, 20, finalY + 46);
  
  if (statement.unpaidAmount) {
    doc.text(`Unpaid Amount: ${statement.unpaidAmount.toLocaleString()} KRW`, 20, finalY + 53);
  }
  
  if (statement.lateFee) {
    doc.text(`Late Fee: ${statement.lateFee.toLocaleString()} KRW`, 20, finalY + 60);
  }
  
  doc.setFontSize(14);
  doc.setFont('helvetica', 'bold');
  doc.text(`Total Amount: ${statement.amount?.toLocaleString() || '0'} KRW`, 20, finalY + 70);
  
  // Download
  const fileName = `billing-statement-${statement.month || 'unknown'}.pdf`;
  doc.save(fileName);
}

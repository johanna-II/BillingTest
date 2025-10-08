/**
 * Statement Display Component
 * Shows calculated billing statement with detailed breakdown
 */

'use client'

import React from 'react'
import { useCalculatedStatement, useBillingLoading } from '@/contexts/BillingContext'
import { format } from 'date-fns'
import { generateStatementPDF } from '@/lib/pdf/statementPDF'

interface StatementDisplayProps {
  onProceedToPayment: () => void
}

const StatementDisplay: React.FC<StatementDisplayProps> = ({ onProceedToPayment }) => {
  const statement = useCalculatedStatement()
  const { isCalculating } = useBillingLoading()

  if (isCalculating) {
    return (
      <div className="kinfolk-card p-12 text-center fade-in">
        <div className="spinner mx-auto mb-4" />
        <p className="text-sm text-kinfolk-gray-600">Calculating billing...</p>
      </div>
    )
  }

  if (!statement) {
    return (
      <div className="kinfolk-card p-12 text-center">
        <p className="text-sm text-kinfolk-gray-600">No statement calculated yet.</p>
      </div>
    )
  }

  const formatCurrency = (amount: number): string => {
    return `₩${amount.toLocaleString('ko-KR')}`
  }

  return (
    <div className="kinfolk-card p-8 md:p-12 fade-in">
      {/* Header */}
      <div className="mb-8 pb-6 border-b-2 border-kinfolk-gray-900">
        <h2 className="text-3xl font-kinfolk-serif mb-2">Billing Statement</h2>
        <p className="text-sm text-kinfolk-gray-600">
          Statement ID: {statement.statementId}
        </p>
      </div>

      {/* Summary Info */}
      <div className="mb-8 p-6 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="kinfolk-label">Billing Month</p>
            <p className="text-sm font-medium">{statement.month}</p>
          </div>
          <div>
            <p className="kinfolk-label">Billing Group</p>
            <p className="text-sm font-medium">{statement.billingGroupId}</p>
          </div>
          <div>
            <p className="kinfolk-label">Status</p>
            <p className="text-sm">
              <span
                className={`
                  px-2 py-1 text-xs uppercase tracking-widest
                  ${
                    statement.status === 'PAID'
                      ? 'bg-green-100 text-green-800'
                      : statement.status === 'OVERDUE'
                      ? 'bg-red-100 text-red-800'
                      : 'bg-yellow-100 text-yellow-800'
                  }
                `}
              >
                {statement.status}
              </span>
            </p>
          </div>
          <div>
            <p className="kinfolk-label">Due Date</p>
            <p className="text-sm font-medium">{format(statement.dueDate, 'PP')}</p>
          </div>
        </div>
      </div>

      {/* Detailed Line Items - Usage & Adjustments */}
      {statement.lineItems && statement.lineItems.length > 0 && (
        <div className="mb-8">
          <h3 className="kinfolk-subheading mb-4">Billing Details</h3>
          <div className="bg-white border border-kinfolk-gray-200">
            <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-kinfolk-gray-50 border-b border-kinfolk-gray-200 text-xs uppercase tracking-widest text-kinfolk-gray-600">
              <div className="col-span-4">Description</div>
              <div className="col-span-2 text-right">Quantity</div>
              <div className="col-span-2 text-right">Unit Price</div>
              <div className="col-span-2 text-right">Type</div>
              <div className="col-span-2 text-right">Amount</div>
            </div>

            {/* Usage Line Items */}
            {statement.lineItems.map((item, index) => (
              <div
                key={item.id}
                className="grid grid-cols-12 gap-4 px-4 py-4 text-sm border-b border-kinfolk-gray-100"
              >
                <div className="col-span-4">
                  <p className="font-medium text-kinfolk-gray-900">{item.counterName}</p>
                  {item.resourceName && (
                    <p className="text-xs text-kinfolk-gray-600 mt-1">{item.resourceName}</p>
                  )}
                  {item.projectId && (
                    <p className="text-xs text-kinfolk-gray-500 mt-1">Project: {item.projectId}</p>
                  )}
                </div>
                <div className="col-span-2 text-right">
                  <p className="font-medium font-kinfolk">{item.quantity.toLocaleString()}</p>
                  <p className="text-xs text-kinfolk-gray-600">{item.unit}</p>
                </div>
                <div className="col-span-2 text-right">
                  <p className="font-medium font-kinfolk">{formatCurrency(item.unitPrice)}</p>
                </div>
                <div className="col-span-2 text-right">
                  <span className="text-xs px-2 py-1 bg-kinfolk-gray-100 text-kinfolk-gray-700 uppercase">
                    {item.counterType}
                  </span>
                </div>
                <div className="col-span-2 text-right">
                  <p className="font-semibold font-kinfolk">{formatCurrency(item.amount)}</p>
                </div>
              </div>
            ))}

            {/* Subtotal Row */}
            <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-kinfolk-beige-50 border-b-2 border-kinfolk-gray-300">
              <div className="col-span-8">
                <p className="font-semibold text-kinfolk-gray-900">Subtotal (Usage)</p>
              </div>
              <div className="col-span-2"></div>
              <div className="col-span-2 text-right">
                <p className="font-bold text-lg font-kinfolk">{formatCurrency(statement.subtotal)}</p>
              </div>
            </div>

            {/* Applied Adjustments (Discounts/Surcharges) */}
            {statement.appliedAdjustments && statement.appliedAdjustments.length > 0 && (
              <>
                {statement.appliedAdjustments.map((adj) => (
                  <div
                    key={adj.adjustmentId}
                    className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-kinfolk-gray-100 bg-green-50"
                  >
                    <div className="col-span-4">
                      <p className="font-medium text-kinfolk-gray-900">{adj.description}</p>
                      <p className="text-xs text-kinfolk-gray-600 mt-1">
                        <span className="uppercase">{adj.type}</span>
                        {' · '}
                        <span className="uppercase">{adj.level}</span>
                        {adj.targetId && ` · Target: ${adj.targetId}`}
                      </p>
                    </div>
                    <div className="col-span-2 text-right">
                      <p className="text-xs text-kinfolk-gray-600">—</p>
                    </div>
                    <div className="col-span-2 text-right">
                      <p className="text-xs text-kinfolk-gray-600">—</p>
                    </div>
                    <div className="col-span-2 text-right">
                      <span className={`text-xs px-2 py-1 uppercase ${
                        adj.type === 'DISCOUNT' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                      }`}>
                        {adj.type}
                      </span>
                    </div>
                    <div className="col-span-2 text-right">
                      <p className={`font-semibold font-kinfolk ${
                        adj.type === 'DISCOUNT' ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {adj.type === 'DISCOUNT' ? '-' : '+'}
                        {formatCurrency(Math.abs(adj.amount))}
                      </p>
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Applied Credits */}
            {statement.appliedCredits && statement.appliedCredits.length > 0 && (
              <>
                {statement.appliedCredits.map((credit) => (
                  <div
                    key={credit.creditId}
                    className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-kinfolk-gray-100 bg-blue-50"
                  >
                    <div className="col-span-4">
                      <p className="font-medium text-kinfolk-gray-900">
                        <span className="uppercase text-xs px-2 py-1 bg-blue-100 text-blue-800 mr-2">
                          {credit.type}
                        </span>
                        {credit.campaignName || 'Credit Applied'}
                      </p>
                      {credit.campaignId && (
                        <p className="text-xs text-kinfolk-gray-600 mt-1">Campaign: {credit.campaignId}</p>
                      )}
                      <p className="text-xs text-kinfolk-gray-500 mt-1 font-kinfolk">
                        Remaining: {formatCurrency(credit.remainingBalance)}
                      </p>
                    </div>
                    <div className="col-span-2 text-right">
                      <p className="text-xs text-kinfolk-gray-600">—</p>
                    </div>
                    <div className="col-span-2 text-right">
                      <p className="text-xs text-kinfolk-gray-600">—</p>
                    </div>
                    <div className="col-span-2 text-right">
                      <span className="text-xs px-2 py-1 bg-blue-100 text-blue-800 uppercase">
                        CREDIT
                      </span>
                    </div>
                    <div className="col-span-2 text-right">
                      <p className="font-semibold text-blue-600 font-kinfolk">
                        -{formatCurrency(credit.amountApplied)}
                      </p>
                    </div>
                  </div>
                ))}
              </>
            )}

            {/* Other Charges */}
            {statement.unpaidAmount > 0 && (
              <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-kinfolk-gray-100 bg-red-50">
                <div className="col-span-4">
                  <p className="font-medium text-kinfolk-gray-900">Unpaid Amount</p>
                  <p className="text-xs text-kinfolk-gray-600 mt-1">From previous billing period</p>
                </div>
                <div className="col-span-2 text-right">
                  <p className="text-xs text-kinfolk-gray-600">—</p>
                </div>
                <div className="col-span-2 text-right">
                  <p className="text-xs text-kinfolk-gray-600">—</p>
                </div>
                <div className="col-span-2 text-right">
                  <span className="text-xs px-2 py-1 bg-red-100 text-red-800 uppercase">
                    OVERDUE
                  </span>
                </div>
                <div className="col-span-2 text-right">
                  <p className="font-semibold text-red-600 font-kinfolk">
                    +{formatCurrency(statement.unpaidAmount)}
                  </p>
                </div>
              </div>
            )}

            {statement.lateFee > 0 && (
              <div className="grid grid-cols-12 gap-4 px-4 py-3 border-b border-kinfolk-gray-100 bg-red-50">
                <div className="col-span-4">
                  <p className="font-medium text-kinfolk-gray-900">Late Fee</p>
                  <p className="text-xs text-kinfolk-gray-600 mt-1">5% penalty on overdue amount</p>
                </div>
                <div className="col-span-2 text-right">
                  <p className="text-xs text-kinfolk-gray-600">—</p>
                </div>
                <div className="col-span-2 text-right">
                  <p className="text-xs text-kinfolk-gray-600">—</p>
                </div>
                <div className="col-span-2 text-right">
                  <span className="text-xs px-2 py-1 bg-red-100 text-red-800 uppercase">
                    PENALTY
                  </span>
                </div>
                <div className="col-span-2 text-right">
                  <p className="font-semibold text-red-600 font-kinfolk">
                    +{formatCurrency(statement.lateFee)}
                  </p>
                </div>
              </div>
            )}

            {/* VAT Row */}
            <div className="grid grid-cols-12 gap-4 px-4 py-3 bg-kinfolk-gray-50 border-b border-kinfolk-gray-200">
              <div className="col-span-8">
                <p className="font-medium text-kinfolk-gray-900">VAT (10%)</p>
              </div>
              <div className="col-span-2"></div>
              <div className="col-span-2 text-right">
                <p className="font-semibold font-kinfolk">
                  +{formatCurrency(Math.round((statement.totalAmount - (statement.subtotal + statement.adjustmentTotal - statement.creditApplied + statement.unpaidAmount + statement.lateFee)) * 10) / 10)}
                </p>
              </div>
            </div>

            {/* Total Row */}
            <div className="grid grid-cols-12 gap-4 px-4 py-4 bg-kinfolk-gray-900 text-white">
              <div className="col-span-8">
                <p className="text-xl font-kinfolk-serif">Total Amount Due</p>
              </div>
              <div className="col-span-2"></div>
              <div className="col-span-2 text-right">
                <p className="text-2xl font-bold font-kinfolk">{formatCurrency(statement.totalAmount)}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Total Summary */}
      <div className="mb-8">
        <div className="bg-kinfolk-beige-50 border-2 border-kinfolk-gray-900 p-6">
          <div className="space-y-3">
            <div className="flex justify-between items-center text-sm">
              <span className="text-kinfolk-gray-700">Subtotal (Usage)</span>
          <span className="font-medium font-kinfolk">{formatCurrency(statement.subtotal)}</span>
        </div>

        {statement.adjustmentTotal !== 0 && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-kinfolk-gray-700">Adjustments</span>
                <span className={`font-kinfolk ${statement.adjustmentTotal < 0 ? 'text-green-600 font-medium' : 'text-red-600 font-medium'}`}>
              {statement.adjustmentTotal > 0 ? '+' : ''}
              {formatCurrency(statement.adjustmentTotal)}
            </span>
          </div>
        )}

        {statement.creditApplied > 0 && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-kinfolk-gray-700">Credits Applied</span>
                <span className="text-green-600 font-medium font-kinfolk">-{formatCurrency(statement.creditApplied)}</span>
          </div>
        )}

        {statement.unpaidAmount > 0 && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-kinfolk-gray-700">Previous Unpaid</span>
                <span className="text-red-600 font-medium font-kinfolk">+{formatCurrency(statement.unpaidAmount)}</span>
          </div>
        )}

        {statement.lateFee > 0 && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-kinfolk-gray-700">Late Fee</span>
                <span className="text-red-600 font-medium font-kinfolk">+{formatCurrency(statement.lateFee)}</span>
          </div>
        )}

            <div className="border-t-2 border-kinfolk-gray-300 pt-3 mt-3">
              <div className="flex justify-between items-center">
                <span className="text-xl font-kinfolk-serif">Total Amount Due</span>
                <span className="text-3xl font-semibold font-kinfolk">{formatCurrency(statement.totalAmount)}</span>
                </div>
            </div>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex flex-col sm:flex-row gap-4 justify-center">
        <button
          onClick={() => generateStatementPDF(statement)}
          className="kinfolk-button-secondary"
        >
          Download PDF
        </button>
        <button onClick={onProceedToPayment} className="kinfolk-button">
          Proceed to Payment
        </button>
      </div>
    </div>
  )
}

export default React.memo(StatementDisplay)


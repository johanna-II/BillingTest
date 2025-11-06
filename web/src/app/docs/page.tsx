/**
 * Documentation Page - KINFOLK Style
 * Features and frontend integration guide
 */

'use client'

import React from 'react'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

export default function DocsPage() {
  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="flex-1 bg-kinfolk-beige-50">
        <div className="kinfolk-container py-16">
          {/* Hero */}
          <div className="mb-16 text-center">
            <h1 className="text-4xl md:text-5xl font-kinfolk-serif mb-4">Documentation</h1>
            <p className="text-lg text-kinfolk-gray-600">
              Complete guide to the Billing Calculator
            </p>
          </div>

          {/* Table of Contents */}
          <div className="kinfolk-card p-8 mb-12">
            <h2 className="kinfolk-subheading mb-6">Contents</h2>
            <nav className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <a href="#overview" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → Overview
              </a>
              <a href="#features" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → Features
              </a>
              <a href="#getting-started" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → Getting Started
              </a>
              <a href="#api-integration" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → API Integration
              </a>
              <a href="#architecture" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → System Architecture
              </a>
              <a href="#sequence-diagram" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → Sequence Diagram
              </a>
              <a href="#billing-flow" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → Billing Flow
              </a>
              <a href="#examples" className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors">
                → Code Examples
              </a>
            </nav>
          </div>

          {/* Overview */}
          <section id="overview" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">Overview</h2>
              <div className="space-y-4 text-kinfolk-gray-700 leading-relaxed">
                <p>
                  The Billing Calculator is a modern web application designed for calculating and testing
                  complex billing scenarios. Built with Next.js, TypeScript, and a KINFOLK-inspired minimal design.
                </p>
                <p>
                  It provides a comprehensive solution for managing usage-based billing, adjustments,
                  credits, and payment processing with real-time calculations and PDF export capabilities.
                </p>
              </div>
            </div>
          </section>

          {/* Features */}
          <section id="features" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">Features</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                <div>
                  <h3 className="kinfolk-subheading mb-4">Core Features</h3>
                  <ul className="space-y-3 text-sm text-kinfolk-gray-700">
                    <li>✓ Usage-based billing calculation</li>
                    <li>✓ Multiple instance types support</li>
                    <li>✓ Adjustments (discounts & surcharges)</li>
                    <li>✓ Credit management</li>
                    <li>✓ Unpaid amount & late fee handling</li>
                    <li>✓ VAT calculation (10%)</li>
                  </ul>
                </div>
                <div>
                  <h3 className="kinfolk-subheading mb-4">Advanced Features</h3>
                  <ul className="space-y-3 text-sm text-kinfolk-gray-700">
                    <li>✓ PDF statement export</li>
                    <li>✓ Calculation history (50 entries)</li>
                    <li>✓ Mock payment processing</li>
                    <li>✓ Real-time calculations</li>
                    <li>✓ Data visualization charts</li>
                    <li>✓ Scenario comparison</li>
                  </ul>
                </div>
              </div>
            </div>
          </section>

          {/* Getting Started */}
          <section id="getting-started" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">Getting Started</h2>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">1. Basic Information</h3>
                <p className="text-sm text-kinfolk-gray-700 mb-4">
                  Start by entering the basic billing information:
                </p>
                <ul className="space-y-2 text-sm text-kinfolk-gray-700 ml-4">
                  <li>• <strong>Target Date</strong>: Billing month</li>
                  <li>• <strong>UUID</strong>: Unique identifier for the billing entity</li>
                  <li>• <strong>Billing Group ID</strong>: Group identifier</li>
                  <li>• <strong>Unpaid Amount</strong>: Previous period unpaid balance</li>
                  <li>• <strong>Is Overdue</strong>: Apply late fee (5%)</li>
                </ul>
              </div>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">2. Add Usage Entries</h3>
                <p className="text-sm text-kinfolk-gray-700 mb-4">
                  Add resource usage with available instance types:
                </p>
                <div className="bg-kinfolk-beige-50 p-4 text-sm text-kinfolk-gray-700 space-y-2">
                  <p>• <strong>compute.c2.c8m8</strong> - ₩397/hour</p>
                  <p>• <strong>compute.g2.t4.c8m64</strong> - ₩166.67/hour</p>
                  <p>• <strong>storage.volume.ssd</strong> - ₩100/GB/month</p>
                  <p>• <strong>network.floating_ip</strong> - ₩25/hour</p>
                </div>
              </div>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">3. Apply Adjustments (Optional)</h3>
                <p className="text-sm text-kinfolk-gray-700 mb-4">
                  Add discounts or surcharges:
                </p>
                <ul className="space-y-2 text-sm text-kinfolk-gray-700 ml-4">
                  <li>• <strong>Type</strong>: DISCOUNT or SURCHARGE</li>
                  <li>• <strong>Level</strong>: BILLING_GROUP or PROJECT</li>
                  <li>• <strong>Method</strong>: RATE (%) or FIXED (amount)</li>
                </ul>
              </div>

              <div>
                <h3 className="kinfolk-subheading mb-4">4. Add Credits (Optional)</h3>
                <p className="text-sm text-kinfolk-gray-700 mb-4">
                  Apply credits to reduce billing amount:
                </p>
                <ul className="space-y-2 text-sm text-kinfolk-gray-700 ml-4">
                  <li>• <strong>FREE</strong>: Free promotional credits</li>
                  <li>• <strong>PAID</strong>: Pre-purchased credits</li>
                  <li>• <strong>PROMOTIONAL</strong>: Campaign credits</li>
                </ul>
              </div>
            </div>
          </section>

          {/* API Integration */}
          <section id="api-integration" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">API Integration</h2>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">Frontend API Client</h3>
                <p className="text-sm text-kinfolk-gray-700 mb-4">
                  The application uses Next.js API routes as a proxy to avoid CORS issues:
                </p>
                <pre className="bg-kinfolk-gray-900 text-white p-4 text-xs overflow-x-auto rounded">
{`import { calculateBilling } from '@/lib/api/billing-api'

// Calculate billing
const statement = await calculateBilling({
  targetDate: new Date('2025-01'),
  uuid: 'test-uuid-001',
  billingGroupId: 'bg-kr-test',
  usage: [...],
  credits: [...],
  adjustments: [...],
  unpaidAmount: 0,
  isOverdue: false
})`}
                </pre>
              </div>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">Backend Endpoints</h3>
                <div className="space-y-4">
                  <div className="border-l-2 border-kinfolk-gray-900 pl-4">
                    <p className="text-xs uppercase tracking-widest text-kinfolk-gray-600 mb-2">POST</p>
                    <p className="text-sm font-mono text-kinfolk-gray-900 mb-2">/billing/meters</p>
                    <p className="text-sm text-kinfolk-gray-700">Send metering data</p>
                  </div>
                  <div className="border-l-2 border-kinfolk-gray-900 pl-4">
                    <p className="text-xs uppercase tracking-widest text-kinfolk-gray-600 mb-2">POST</p>
                    <p className="text-sm font-mono text-kinfolk-gray-900 mb-2">/billing/admin/calculate</p>
                    <p className="text-sm text-kinfolk-gray-700">Trigger billing calculation</p>
                  </div>
                  <div className="border-l-2 border-kinfolk-gray-900 pl-4">
                    <p className="text-xs uppercase tracking-widest text-kinfolk-gray-600 mb-2">GET</p>
                    <p className="text-sm font-mono text-kinfolk-gray-900 mb-2">/billing/payments/{'{month}'}/statements</p>
                    <p className="text-sm text-kinfolk-gray-700">Fetch billing statement</p>
                  </div>
                  <div className="border-l-2 border-kinfolk-gray-900 pl-4">
                    <p className="text-xs uppercase tracking-widest text-kinfolk-gray-600 mb-2">POST</p>
                    <p className="text-sm font-mono text-kinfolk-gray-900 mb-2">/billing/payments/{'{month}'}</p>
                    <p className="text-sm text-kinfolk-gray-700">Process payment</p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* System Architecture */}
          <section id="architecture" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">System Architecture</h2>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-6">Architecture Diagram</h3>
                <div className="bg-kinfolk-beige-50 p-8 border border-kinfolk-gray-200">
                  <div className="space-y-6">
                    {/* Frontend */}
                    <div className="bg-white p-6 border-2 border-kinfolk-gray-900">
                      <h4 className="text-sm font-bold mb-3 uppercase tracking-widest">Frontend (Next.js)</h4>
                      <div className="grid grid-cols-3 gap-4 text-xs text-kinfolk-gray-700">
                        <div className="p-3 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
                          <div className="font-medium mb-1">React Components</div>
                          <div>UI Layer</div>
                        </div>
                        <div className="p-3 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
                          <div className="font-medium mb-1">Context API</div>
                          <div>State Management</div>
                        </div>
                        <div className="p-3 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
                          <div className="font-medium mb-1">React Query</div>
                          <div>Data Fetching</div>
                        </div>
                      </div>
                    </div>

                    {/* Arrow */}
                    <div className="flex justify-center">
                      <div className="text-2xl text-kinfolk-gray-400">↓</div>
                    </div>

                    {/* Next.js API Routes */}
                    <div className="bg-white p-6 border-2 border-kinfolk-gray-700">
                      <h4 className="text-sm font-bold mb-3 uppercase tracking-widest">Next.js API Routes (Proxy)</h4>
                      <div className="text-xs text-kinfolk-gray-700">
                        <div className="mb-2 font-medium">CORS 해결 및 요청 중계</div>
                        <div className="font-mono bg-kinfolk-beige-50 p-2">/api/billing/*</div>
                      </div>
                    </div>

                    {/* Arrow */}
                    <div className="flex justify-center">
                      <div className="text-2xl text-kinfolk-gray-400">↓</div>
                    </div>

                    {/* Backend */}
                    <div className="bg-white p-6 border-2 border-kinfolk-gray-900">
                      <h4 className="text-sm font-bold mb-3 uppercase tracking-widest">Backend (Flask Mock Server)</h4>
                      <div className="grid grid-cols-4 gap-3 text-xs text-kinfolk-gray-700">
                        <div className="p-3 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
                          <div className="font-medium mb-1">Metering</div>
                          <div>Usage Data</div>
                        </div>
                        <div className="p-3 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
                          <div className="font-medium mb-1">Calculation</div>
                          <div>Billing Logic</div>
                        </div>
                        <div className="p-3 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
                          <div className="font-medium mb-1">Statements</div>
                          <div>Results</div>
                        </div>
                        <div className="p-3 bg-kinfolk-beige-50 border border-kinfolk-gray-200">
                          <div className="font-medium mb-1">Payments</div>
                          <div>Processing</div>
                        </div>
                      </div>
                    </div>

                    {/* Arrow */}
                    <div className="flex justify-center">
                      <div className="text-2xl text-kinfolk-gray-400">↓</div>
                    </div>

                    {/* Data Storage */}
                    <div className="bg-white p-4 border border-kinfolk-gray-300">
                      <h4 className="text-sm font-bold mb-2 uppercase tracking-widest">Data Storage</h4>
                      <div className="text-xs text-kinfolk-gray-700">
                        In-Memory Storage (Mock Server) / LocalStorage (History)
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Sequence Diagram */}
          <section id="sequence-diagram" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">Sequence Diagram</h2>
              <p className="text-sm text-kinfolk-gray-700 mb-8">
                Complete billing calculation request flow
              </p>

              <div className="bg-kinfolk-beige-50 p-8 border border-kinfolk-gray-200 overflow-x-auto">
                <div className="min-w-[900px]">
                  {/* Actors Header */}
                  <div className="grid grid-cols-4 gap-8 mb-12">
                    <div className="text-center">
                      <div className="w-32 h-20 mx-auto bg-kinfolk-gray-900 text-white flex items-center justify-center mb-4 border-2 border-kinfolk-gray-900">
                        <span className="text-sm font-bold">User</span>
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="w-32 h-20 mx-auto bg-kinfolk-gray-700 text-white flex items-center justify-center mb-4 border-2 border-kinfolk-gray-700">
                        <span className="text-sm font-bold">Frontend</span>
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="w-32 h-20 mx-auto bg-kinfolk-gray-700 text-white flex items-center justify-center mb-4 border-2 border-kinfolk-gray-700">
                        <span className="text-sm font-bold">API Proxy</span>
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="w-32 h-20 mx-auto bg-kinfolk-gray-900 text-white flex items-center justify-center mb-4 border-2 border-kinfolk-gray-900">
                        <span className="text-sm font-bold">Backend</span>
                      </div>
                    </div>
                  </div>

                  {/* Messages */}
                  <div className="space-y-8">
                    {/* 1. User -> Frontend */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-kinfolk-gray-900 relative">
                          <div className="absolute right-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-l-[8px] border-transparent border-l-kinfolk-gray-900 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div className="col-span-2"></div>
                      <div className="col-span-4 -mt-10 text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        1. Enter billing data
                      </div>
                    </div>

                    {/* 2. Frontend -> API Proxy */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-kinfolk-gray-900 relative">
                          <div className="absolute right-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-l-[8px] border-transparent border-l-kinfolk-gray-900 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div></div>
                      <div className="col-span-4 -mt-10 ml-[25%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        2. POST /api/billing/meters
                      </div>
                    </div>

                    {/* 3. API Proxy -> Backend */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div className="col-span-2"></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-kinfolk-gray-900 relative">
                          <div className="absolute right-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-l-[8px] border-transparent border-l-kinfolk-gray-900 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div className="col-span-4 -mt-10 ml-[50%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        3. Forward to backend
                      </div>
                    </div>

                    {/* 4. Backend processes */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div className="col-span-3"></div>
                      <div className="text-xs text-kinfolk-gray-700 bg-white p-3 border-2 border-kinfolk-gray-900 text-center">
                        4. Store metering data
                      </div>
                    </div>

                    {/* 5. Frontend -> API Proxy */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-kinfolk-gray-900 relative">
                          <div className="absolute right-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-l-[8px] border-transparent border-l-kinfolk-gray-900 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div></div>
                      <div className="col-span-4 -mt-10 ml-[25%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        5. POST /admin/calculate
                      </div>
                    </div>

                    {/* 6. API Proxy -> Backend */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div className="col-span-2"></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-kinfolk-gray-900 relative">
                          <div className="absolute right-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-l-[8px] border-transparent border-l-kinfolk-gray-900 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div className="col-span-4 -mt-10 ml-[50%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        6. Calculate billing
                      </div>
                    </div>

                    {/* 7. Frontend -> API Proxy */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-kinfolk-gray-900 relative">
                          <div className="absolute right-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-l-[8px] border-transparent border-l-kinfolk-gray-900 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div></div>
                      <div className="col-span-4 -mt-10 ml-[25%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        7. GET /statements
                      </div>
                    </div>

                    {/* 8. API Proxy -> Backend */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div className="col-span-2"></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-kinfolk-gray-900 relative">
                          <div className="absolute right-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-l-[8px] border-transparent border-l-kinfolk-gray-900 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div className="col-span-4 -mt-10 ml-[50%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        8. Fetch statement
                      </div>
                    </div>

                    {/* 9. Backend -> API Proxy (Return) */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div className="col-span-2"></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-dashed border-kinfolk-gray-600 relative">
                          <div className="absolute left-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-r-[8px] border-transparent border-r-kinfolk-gray-600 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div className="col-span-4 -mt-10 ml-[50%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        9. Return statement
                      </div>
                    </div>

                    {/* 10. API Proxy -> Frontend (Return) */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div></div>
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-dashed border-kinfolk-gray-600 relative">
                          <div className="absolute left-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-r-[8px] border-transparent border-r-kinfolk-gray-600 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div></div>
                      <div className="col-span-4 -mt-10 ml-[25%] text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        10. Return to frontend
                      </div>
                    </div>

                    {/* 11. Frontend -> User (Display) */}
                    <div className="grid grid-cols-4 gap-8 items-center">
                      <div className="col-span-2 flex items-center">
                        <div className="w-full border-t-2 border-dashed border-kinfolk-gray-600 relative">
                          <div className="absolute left-0 top-0 w-0 h-0 border-t-[6px] border-b-[6px] border-r-[8px] border-transparent border-r-kinfolk-gray-600 transform -translate-y-1/2"></div>
                        </div>
                      </div>
                      <div className="col-span-2"></div>
                      <div className="col-span-4 -mt-10 text-xs text-kinfolk-gray-700 bg-kinfolk-beige-50 inline-block px-3 py-1 border border-kinfolk-gray-300">
                        11. Display statement
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Billing Flow */}
          <section id="billing-flow" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">Billing Flow</h2>

              <div className="space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-kinfolk-gray-900 text-white flex items-center justify-center text-sm font-bold">1</div>
                  <div className="flex-1">
                    <h4 className="font-medium mb-2">Metering Data Collection</h4>
                    <p className="text-sm text-kinfolk-gray-700">
                      Usage data is sent to the backend with counter information (name, type, volume, unit)
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-kinfolk-gray-900 text-white flex items-center justify-center text-sm font-bold">2</div>
                  <div className="flex-1">
                    <h4 className="font-medium mb-2">Calculation Trigger</h4>
                    <p className="text-sm text-kinfolk-gray-700">
                      Backend calculates subtotal based on usage, applies adjustments and credits
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-kinfolk-gray-900 text-white flex items-center justify-center text-sm font-bold">3</div>
                  <div className="flex-1">
                    <h4 className="font-medium mb-2">Statement Generation</h4>
                    <p className="text-sm text-kinfolk-gray-700">
                      Complete statement with line items, adjustments, credits, unpaid amount, and late fee
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-kinfolk-gray-900 text-white flex items-center justify-center text-sm font-bold">4</div>
                  <div className="flex-1">
                    <h4 className="font-medium mb-2">VAT & Final Amount</h4>
                    <p className="text-sm text-kinfolk-gray-700">
                      10% VAT is applied to calculate the final total amount due
                    </p>
                  </div>
                </div>

                <div className="flex items-start space-x-4">
                  <div className="w-8 h-8 bg-kinfolk-gray-900 text-white flex items-center justify-center text-sm font-bold">5</div>
                  <div className="flex-1">
                    <h4 className="font-medium mb-2">Payment Processing</h4>
                    <p className="text-sm text-kinfolk-gray-700">
                      Mock payment is processed and receipt is generated
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </section>

          {/* Code Examples */}
          <section id="examples" className="mb-16">
            <div className="kinfolk-card p-12">
              <h2 className="text-3xl font-kinfolk-serif mb-6">Code Examples</h2>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">React Hook Usage</h3>
                <pre className="bg-kinfolk-gray-900 text-white p-4 text-xs overflow-x-auto rounded">
{`import { useBillingCalculation } from '@/hooks/useBillingCalculation'

function MyComponent() {
  const { mutate: calculate, isLoading } = useBillingCalculation()

  const handleCalculate = () => {
    calculate(billingInput, {
      onSuccess: (statement) => {
        console.log('Statement:', statement)
      },
      onError: (error) => {
        console.error('Error:', error)
      }
    })
  }

  return <button onClick={handleCalculate}>Calculate</button>
}`}
                </pre>
              </div>

              <div className="mb-8">
                <h3 className="kinfolk-subheading mb-4">Context API Usage</h3>
                <pre className="bg-kinfolk-gray-900 text-white p-4 text-xs overflow-x-auto rounded">
{`import { useBilling, useCalculatedStatement } from '@/contexts/BillingContext'

function StatementComponent() {
  const { actions } = useBilling()
  const statement = useCalculatedStatement()

  return (
    <div>
      {statement && (
        <div>Total: {statement.totalAmount}</div>
      )}
    </div>
  )
}`}
                </pre>
              </div>

              <div>
                <h3 className="kinfolk-subheading mb-4">PDF Export</h3>
                <pre className="bg-kinfolk-gray-900 text-white p-4 text-xs overflow-x-auto rounded">
{`import { generateStatementPDF } from '@/lib/pdf/statementPDF'

// Generate and download PDF
generateStatementPDF(statement)`}
                </pre>
              </div>
            </div>
          </section>

          {/* Additional Resources */}
          <div className="kinfolk-card p-8 bg-kinfolk-beige-50 border-2 border-kinfolk-gray-900">
            <h3 className="kinfolk-subheading mb-4">Additional Resources</h3>
            <div className="space-y-3">
              <a href="/api-reference" className="block text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900">
                → View API Reference (Swagger UI)
              </a>
              <a href="https://github.com/johanna-II/BillingTest" target="_blank" rel="noopener noreferrer" className="block text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900">
                → GitHub Repository
              </a>
              <a href="/license" className="block text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900">
                → MIT License
              </a>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

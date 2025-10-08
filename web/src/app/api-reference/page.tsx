/**
 * API Reference Page - KINFOLK Style
 * Swagger UI Integration
 */

'use client'

import React, { useState } from 'react'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

export default function APIReferencePage(): JSX.Element {
  const [swaggerUrl] = useState('http://localhost:5001/docs')

  return (
    <div className="flex flex-col min-h-screen">
      <Header />
      
      <main className="flex-1 bg-kinfolk-beige-50">
        <div className="kinfolk-container py-16">
          {/* Hero */}
          <div className="mb-12 text-center">
            <h1 className="text-4xl md:text-5xl font-kinfolk-serif mb-4">API Reference</h1>
            <p className="text-lg text-kinfolk-gray-600">
              Comprehensive Backend API Documentation
            </p>
          </div>

          {/* Info Card */}
          <div className="kinfolk-card p-8 mb-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="kinfolk-subheading mb-4">Swagger UI</h3>
                <p className="text-sm text-kinfolk-gray-700 leading-relaxed mb-4">
                  Interactive API documentation powered by OpenAPI specification. 
                  Test endpoints directly from your browser.
                </p>
                <div className="space-y-2 text-sm text-kinfolk-gray-700">
                  <p><strong>Base URL:</strong> <code className="bg-kinfolk-beige-50 px-2 py-1">http://localhost:5001</code></p>
                  <p><strong>OpenAPI Version:</strong> 3.0.0</p>
                </div>
              </div>

              <div>
                <h3 className="kinfolk-subheading mb-4">Quick Links</h3>
                <ul className="space-y-2">
                  <li>
                    <a 
                      href="#metering" 
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Metering Endpoints
                    </a>
                  </li>
                  <li>
                    <a 
                      href="#calculation" 
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Calculation Endpoints
                    </a>
                  </li>
                  <li>
                    <a 
                      href="#payments" 
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Payment Endpoints
                    </a>
                  </li>
                  <li>
                    <a 
                      href="#statements" 
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Statement Endpoints
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Swagger UI Container */}
          <div className="kinfolk-card overflow-hidden" style={{ minHeight: '800px' }}>
            <div className="border-b border-kinfolk-gray-200 px-6 py-4 bg-kinfolk-beige-50">
              <div className="flex items-center justify-between">
                <h2 className="kinfolk-subheading mb-0">Interactive API Documentation</h2>
                <a 
                  href={swaggerUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-xs uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900"
                >
                  Open in New Tab ↗
                </a>
              </div>
            </div>
            <iframe
              src={swaggerUrl}
              className="w-full border-none"
              style={{ height: '1000px', minHeight: '800px' }}
              title="API Documentation"
            />
          </div>

          {/* API Overview */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="kinfolk-card p-6" id="metering">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                M
              </div>
              <h3 className="kinfolk-subheading mb-3">Metering</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Send usage data for billing calculation
              </p>
            </div>

            <div className="kinfolk-card p-6" id="calculation">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                C
              </div>
              <h3 className="kinfolk-subheading mb-3">Calculation</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Trigger billing calculations with adjustments
              </p>
            </div>

            <div className="kinfolk-card p-6" id="payments">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                P
              </div>
              <h3 className="kinfolk-subheading mb-3">Payments</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Process payments and manage transactions
              </p>
            </div>

            <div className="kinfolk-card p-6" id="statements">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                S
              </div>
              <h3 className="kinfolk-subheading mb-3">Statements</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Retrieve detailed billing statements
              </p>
            </div>
          </div>

          {/* Additional Info */}
          <div className="mt-12 kinfolk-card p-8 bg-yellow-50 border border-yellow-200">
            <h3 className="kinfolk-subheading mb-4">Important Notes</h3>
            <ul className="space-y-2 text-sm text-kinfolk-gray-700">
              <li>• Make sure the mock server is running at <code className="bg-white px-2 py-1">http://localhost:5001</code></li>
              <li>• All endpoints require a <code className="bg-white px-2 py-1">uuid</code> header for authentication</li>
              <li>• Use <code className="bg-white px-2 py-1">test-uuid-001</code> for testing purposes</li>
              <li>• The mock server includes sample data for testing various scenarios</li>
            </ul>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

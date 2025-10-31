/**
 * API Reference Page - KINFOLK Style
 * Swagger UI Integration (Self-hosted)
 */

'use client'

import React, { useState } from 'react'
import dynamic from 'next/dynamic'
import Header from '@/components/Header'
import Footer from '@/components/Footer'
import 'swagger-ui-react/swagger-ui.css'

// Dynamically import SwaggerUI to avoid SSR issues
const SwaggerUI = dynamic(() => import('swagger-ui-react'), { ssr: false })

export default function APIReferencePage(): JSX.Element {
  const [isLoaded, setIsLoaded] = useState(true)

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
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div>
                <h3 className="kinfolk-subheading mb-4">Swagger UI</h3>
                <p className="text-sm text-kinfolk-gray-700 leading-relaxed mb-4">
                  Interactive API documentation powered by OpenAPI specification.
                  Test endpoints directly from your browser.
                </p>
                <div className="space-y-2 text-sm text-kinfolk-gray-700">
                  <p><strong>OpenAPI Version:</strong> 3.0.3</p>
                  <p className="text-xs text-kinfolk-gray-600 mt-3 bg-green-50 border border-green-200 px-3 py-2">
                    ⚡ Always available - 24/7 documentation access
                  </p>
                </div>
              </div>

              <div>
                <h3 className="kinfolk-subheading mb-4">Server Selection</h3>
                <div className="space-y-3 text-sm text-kinfolk-gray-700">
                  <div className="bg-kinfolk-beige-50 p-3 border border-kinfolk-gray-300">
                    <div className="font-medium mb-1">Next.js API Routes (Recommended)</div>
                    <code className="text-xs">http://localhost:3000/api</code>
                    <div className="text-xs text-kinfolk-gray-600 mt-1">
                      ✓ Always available with dev server
                    </div>
                  </div>
                  <div className="bg-white p-3 border border-kinfolk-gray-300">
                    <div className="font-medium mb-1">Mock Server (Direct)</div>
                    <code className="text-xs">http://localhost:5001</code>
                    <div className="text-xs text-kinfolk-gray-600 mt-1">
                      Requires mock server running
                    </div>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="kinfolk-subheading mb-4">Quick Links</h3>
                <ul className="space-y-2">
                  <li>
                    <a
                      href="#contracts"
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Contract Management
                    </a>
                  </li>
                  <li>
                    <a
                      href="#credits"
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Credits & Adjustments
                    </a>
                  </li>
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
                      href="#payments"
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Payment Processing
                    </a>
                  </li>
                  <li>
                    <a
                      href="#batch"
                      className="text-sm text-kinfolk-gray-700 hover:text-kinfolk-gray-900 transition-colors"
                    >
                      → Batch Operations
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </div>

          {/* Swagger UI Container */}
          <div className="kinfolk-card overflow-hidden">
            <div className="border-b border-kinfolk-gray-200 px-6 py-4 bg-kinfolk-beige-50">
              <h2 className="kinfolk-subheading mb-0">Interactive API Documentation</h2>
            </div>
            <div className="bg-white">
              {isLoaded ? (
                <SwaggerUI
                  url="/openapi.yaml"
                  docExpansion="list"
                  defaultModelsExpandDepth={1}
                  displayRequestDuration={true}
                  filter={true}
                />
              ) : (
                <div className="p-12 text-center">
                  <div className="spinner mx-auto mb-4" />
                  <p className="text-sm text-kinfolk-gray-600">Loading API Documentation...</p>
                </div>
              )}
            </div>
          </div>

          {/* API Overview */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
            <div className="kinfolk-card p-6" id="contracts">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                C
              </div>
              <h3 className="kinfolk-subheading mb-3">Contracts</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Manage billing contracts and agreements
              </p>
            </div>

            <div className="kinfolk-card p-6" id="credits">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                $
              </div>
              <h3 className="kinfolk-subheading mb-3">Credits</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Grant and manage billing credits
              </p>
            </div>

            <div className="kinfolk-card p-6" id="metering">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                M
              </div>
              <h3 className="kinfolk-subheading mb-3">Metering</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Send usage data for billing calculation
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

            <div className="kinfolk-card p-6" id="batch">
              <div className="w-12 h-12 bg-kinfolk-gray-900 text-white flex items-center justify-center text-lg font-bold mb-4">
                B
              </div>
              <h3 className="kinfolk-subheading mb-3">Batch</h3>
              <p className="text-sm text-kinfolk-gray-700">
                Batch job operations and monitoring
              </p>
            </div>
          </div>

          {/* How to Test */}
          <div className="mt-12 grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Option 1: Next.js API Routes */}
            <div className="kinfolk-card p-8 bg-green-50 border-2 border-green-300">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-green-600 text-white flex items-center justify-center text-sm font-bold mr-3">1</div>
                <h3 className="kinfolk-subheading mb-0">Recommended: Next.js API Routes</h3>
              </div>
              <ul className="space-y-2 text-sm text-kinfolk-gray-700">
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>Already running with <code className="bg-white px-2 py-1">npm run dev</code></span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>No additional server needed</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">✓</span>
                  <span>CORS automatically handled</span>
                </li>
              </ul>
              <div className="mt-4 pt-4 border-t border-green-300">
                <p className="text-xs font-medium mb-2">How to use:</p>
                <ol className="text-xs text-kinfolk-gray-700 space-y-1 list-decimal list-inside">
                  <li>Select <strong>"Next.js API Routes"</strong> in Swagger UI dropdown</li>
                  <li>Click "Try it out" on any endpoint</li>
                  <li>Add <code className="bg-white px-1">uuid: test-uuid-001</code> header</li>
                  <li>Click "Execute"</li>
                </ol>
              </div>
            </div>

            {/* Option 2: Mock Server Direct */}
            <div className="kinfolk-card p-8 bg-yellow-50 border border-yellow-200">
              <div className="flex items-center mb-4">
                <div className="w-8 h-8 bg-yellow-600 text-white flex items-center justify-center text-sm font-bold mr-3">2</div>
                <h3 className="kinfolk-subheading mb-0">Alternative: Mock Server Direct</h3>
              </div>
              <ul className="space-y-2 text-sm text-kinfolk-gray-700">
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Direct access to backend logic</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Requires separate server process</span>
                </li>
                <li className="flex items-start">
                  <span className="mr-2">•</span>
                  <span>Additional endpoints available</span>
                </li>
              </ul>
              <div className="mt-4 pt-4 border-t border-yellow-300">
                <p className="text-xs font-medium mb-2">Start Mock Server:</p>
                <pre className="bg-kinfolk-gray-900 text-white p-3 text-xs rounded">
{`cd mock_server
python run_server.py`}
                </pre>
                <p className="text-xs text-kinfolk-gray-600 mt-2">
                  Then select <strong>"Mock Server (Direct)"</strong> in dropdown
                </p>
              </div>
            </div>
          </div>

          {/* Usage Guide */}
          <div className="mt-6 kinfolk-card p-8 bg-kinfolk-beige-50 border-2 border-kinfolk-gray-900">
            <h3 className="kinfolk-subheading mb-4">Important Notes</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-kinfolk-gray-700">
              <div>
                <h4 className="font-medium mb-2">Authentication</h4>
                <ul className="space-y-1 text-xs">
                  <li>• All endpoints require <code className="bg-white px-2 py-1">uuid</code> header</li>
                  <li>• Test UUID: <code className="bg-white px-2 py-1">test-uuid-001</code></li>
                  <li>• Each request needs this header for routing</li>
                </ul>
              </div>
              <div>
                <h4 className="font-medium mb-2">Server Dropdown</h4>
                <ul className="space-y-1 text-xs">
                  <li>• Located at top of Swagger UI</li>
                  <li>• Switch between Next.js and Mock Server</li>
                  <li>• Default: Next.js API Routes (Port 3000)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

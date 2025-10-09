/**
 * API Reference Page - KINFOLK Style
 * Swagger UI Integration
 */

'use client'

import React, { useState, useEffect } from 'react'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

export default function APIReferencePage(): JSX.Element {
  // Auto-detect Swagger URL based on environment
  const getSwaggerUrl = (): string => {
    // In production (Cloudflare Pages), use the worker URL
    if (process.env.NEXT_PUBLIC_API_URL) {
      return `${process.env.NEXT_PUBLIC_API_URL}/docs`
    }
    
    // For local development, try port 5001 first (mock server)
    // If not available, fall back to port 8787 (worker dev)
    if (typeof window !== 'undefined') {
      return 'http://localhost:5001/docs'
    }
    
    return 'http://localhost:5001/docs'
  }

  const [swaggerUrl, setSwaggerUrl] = useState(getSwaggerUrl())
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Check if Swagger UI is available
  useEffect(() => {
    const checkSwaggerAvailability = async () => {
      try {
        const response = await fetch(swaggerUrl, { method: 'HEAD' })
        if (!response.ok) {
          throw new Error('Swagger UI not available')
        }
        setIsLoading(false)
      } catch (err) {
        // Try fallback to worker dev server
        const fallbackUrl = 'http://localhost:8787/docs'
        try {
          const fallbackResponse = await fetch(fallbackUrl, { method: 'HEAD' })
          if (fallbackResponse.ok) {
            setSwaggerUrl(fallbackUrl)
            setIsLoading(false)
            return
          }
        } catch {
          // Both failed
        }
        
        setError('Swagger UI server not running. Please start the mock server on port 5001 or the worker dev server.')
        setIsLoading(false)
      }
    }

    checkSwaggerAvailability()
  }, [])

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
                {!error && (
                  <a 
                    href={swaggerUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900"
                  >
                    Open in New Tab ↗
                  </a>
                )}
              </div>
            </div>
            
            {isLoading ? (
              <div className="flex items-center justify-center p-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-kinfolk-gray-900 mx-auto mb-4"></div>
                  <p className="text-kinfolk-gray-600">Loading API Documentation...</p>
                </div>
              </div>
            ) : error ? (
              <div className="p-12">
                <div className="max-w-2xl mx-auto">
                  <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-8">
                    <h3 className="kinfolk-subheading mb-4 text-yellow-800">⚠️ Swagger UI Not Available</h3>
                    <p className="text-sm text-kinfolk-gray-700 mb-4">{error}</p>
                    
                    <div className="bg-white rounded p-4 mb-4">
                      <p className="text-sm font-semibold mb-2">To start the mock server:</p>
                      <code className="text-xs bg-kinfolk-gray-900 text-white px-3 py-2 rounded block">
                        python start_mock_server_simple.py
                      </code>
                    </div>
                    
                    <div className="bg-white rounded p-4">
                      <p className="text-sm font-semibold mb-2">Or start the worker dev server:</p>
                      <code className="text-xs bg-kinfolk-gray-900 text-white px-3 py-2 rounded block">
                        cd workers/billing-api && npm run dev
                      </code>
                    </div>
                    
                    <button 
                      onClick={() => window.location.reload()}
                      className="mt-4 px-4 py-2 bg-kinfolk-gray-900 text-white text-sm hover:bg-kinfolk-gray-800 transition-colors"
                    >
                      Retry Connection
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              <iframe
                src={swaggerUrl}
                className="w-full border-none"
                style={{ height: '1000px', minHeight: '800px' }}
                title="API Documentation"
                sandbox="allow-same-origin allow-scripts allow-forms allow-popups"
              />
            )}
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
              <li>• <strong>Current Swagger URL:</strong> <code className="bg-white px-2 py-1">{swaggerUrl}</code></li>
              <li>• All endpoints require a <code className="bg-white px-2 py-1">uuid</code> header for authentication</li>
              <li>• Use <code className="bg-white px-2 py-1">test-uuid-001</code> for testing purposes</li>
              <li>• The server includes sample data for testing various scenarios</li>
              <li>• For production, set <code className="bg-white px-2 py-1">NEXT_PUBLIC_API_URL</code> in Cloudflare Pages settings</li>
            </ul>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

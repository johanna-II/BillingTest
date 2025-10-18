/**
 * MIT License Page - KINFOLK Style
 */

'use client'

import React from 'react'
import Header from '@/components/Header'
import Footer from '@/components/Footer'

export default function LicensePage(): JSX.Element {
  const currentYear = new Date().getFullYear()

  return (
    <div className="flex flex-col min-h-screen">
      <Header />

      <main className="flex-1 bg-kinfolk-beige-50">
        <div className="kinfolk-container py-16">
          {/* Hero */}
          <div className="mb-12 text-center">
            <h1 className="text-4xl md:text-5xl font-kinfolk-serif mb-4">MIT License</h1>
            <p className="text-lg text-kinfolk-gray-600">
              Open Source Software License
            </p>
          </div>

          {/* License Content */}
          <div className="kinfolk-card p-12">
            <div className="max-w-3xl mx-auto">
              <div className="mb-8 pb-8 border-b border-kinfolk-gray-200">
                <p className="text-sm text-kinfolk-gray-700 leading-relaxed">
                  Copyright © {currentYear} Billing Calculator
                </p>
              </div>

              <div className="space-y-6 text-sm text-kinfolk-gray-700 leading-relaxed">
                <p>
                  Permission is hereby granted, free of charge, to any person obtaining a copy
                  of this software and associated documentation files (the "Software"), to deal
                  in the Software without restriction, including without limitation the rights
                  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
                  copies of the Software, and to permit persons to whom the Software is
                  furnished to do so, subject to the following conditions:
                </p>

                <p>
                  The above copyright notice and this permission notice shall be included in all
                  copies or substantial portions of the Software.
                </p>

                <div className="bg-kinfolk-beige-50 p-6 border-l-4 border-kinfolk-gray-900">
                  <p className="font-medium mb-4">
                    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
                    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
                    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
                  </p>
                  <p>
                    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
                    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
                    OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
                    OR OTHER DEALINGS IN THE SOFTWARE.
                  </p>
                </div>
              </div>

              <div className="mt-12 pt-8 border-t border-kinfolk-gray-200">
                <h3 className="kinfolk-subheading mb-4">What This Means</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-medium mb-3">You Can:</h4>
                    <ul className="space-y-2 text-sm text-kinfolk-gray-700">
                      <li>✓ Use commercially</li>
                      <li>✓ Modify</li>
                      <li>✓ Distribute</li>
                      <li>✓ Use privately</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="text-sm font-medium mb-3">You Must:</h4>
                    <ul className="space-y-2 text-sm text-kinfolk-gray-700">
                      <li>→ Include license</li>
                      <li>→ Include copyright</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Additional Info */}
          <div className="mt-12 kinfolk-card p-8 bg-kinfolk-beige-50 border-2 border-kinfolk-gray-900 text-center">
            <p className="text-sm text-kinfolk-gray-700 mb-4">
              For more information about the MIT License
            </p>
            <a
              href="https://opensource.org/licenses/MIT"
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-kinfolk-gray-900 hover:underline"
            >
              Visit opensource.org ↗
            </a>
          </div>
        </div>
      </main>

      <Footer />
    </div>
  )
}

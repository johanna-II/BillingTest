/**
 * Header Component - Minimal KINFOLK style
 */

'use client'

import React from 'react'
import Link from 'next/link'

const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-kinfolk-gray-200">
      <div className="kinfolk-container py-6">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-3 group">
            {/* Logo Icon */}
            <div className="w-8 h-8 bg-kinfolk-gray-900 flex items-center justify-center rounded transition-transform group-hover:scale-105">
              <svg
                className="w-5 h-5 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                aria-label="Billing Calculator Logo"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h1 className="text-xl font-kinfolk-serif tracking-tight">
              Billing
            </h1>
          </Link>

          <nav className="hidden md:flex items-center space-x-8">
            <Link
              href="/"
              className="text-sm uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
            >
              Calculator
            </Link>
            <Link
              href="/docs"
              className="text-sm uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
            >
              Documentation
            </Link>
            <Link
              href="/api-reference"
              className="text-sm uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
            >
              API Reference
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default React.memo(Header)

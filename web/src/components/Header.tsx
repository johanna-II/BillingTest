/**
 * Header Component - Minimal KINFOLK style
 */

'use client'

import React from 'react'

const Header: React.FC = () => {
  return (
    <header className="bg-white border-b border-kinfolk-gray-200">
      <div className="kinfolk-container py-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 bg-kinfolk-gray-900" />
            <h1 className="text-xl font-kinfolk-serif tracking-tight">
              Billing
            </h1>
          </div>

          <nav className="hidden md:flex items-center space-x-8">
            <a
              href="/"
              className="text-sm uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
            >
              Calculator
            </a>
            <a
              href="/docs"
              className="text-sm uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
            >
              Documentation
            </a>
            <a
              href="/api-reference"
              className="text-sm uppercase tracking-widest text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
            >
              API Reference
            </a>
          </nav>
        </div>
      </div>
    </header>
  )
}

export default React.memo(Header)

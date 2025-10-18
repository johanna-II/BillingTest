/**
 * Footer Component - Minimal KINFOLK style
 */

'use client'

import React from 'react'

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className="bg-white border-t border-kinfolk-gray-200 mt-auto">
      <div className="kinfolk-container py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-8">
          {/* About */}
          <div>
            <h3 className="kinfolk-label mb-4">About</h3>
            <p className="text-sm text-kinfolk-gray-600 leading-relaxed">
              A minimal billing calculator for testing and validation.
              Built with precision and simplicity in mind.
            </p>
          </div>

          {/* Resources */}
          <div>
            <h3 className="kinfolk-label mb-4">Resources</h3>
            <ul className="space-y-2">
              <li>
                <a
                  href="/docs"
                  className="text-sm text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
                >
                  Documentation
                </a>
              </li>
              <li>
                <a
                  href="/api-reference"
                  className="text-sm text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
                >
                  API Reference
                </a>
              </li>
              <li>
                <a
                  href="https://github.com/johanna-II/BillingTest"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-kinfolk-gray-600 hover:text-kinfolk-gray-900 transition-colors"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="kinfolk-label mb-4">Contact</h3>
            <p className="text-sm text-kinfolk-gray-600">
              For support and inquiries
            </p>
            <a
              href="mailto:jane@janetheglory.org"
              className="text-sm text-kinfolk-gray-900 hover:underline"
            >
              jane@janetheglory.org
            </a>
          </div>
        </div>

        <div className="kinfolk-divider" />

        <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
          <p className="text-xs uppercase tracking-widest text-kinfolk-gray-500">
            © {currentYear} Billing Calculator
          </p>
          <a
            href="/license"
            className="text-xs uppercase tracking-widest text-kinfolk-gray-500 hover:text-kinfolk-gray-900 transition-colors"
          >
            MIT License
          </a>
        </div>
      </div>
    </footer>
  )
}

export default React.memo(Footer)

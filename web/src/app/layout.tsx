/**
 * Root Layout - KINFOLK inspired minimal design
 */

import type { Metadata } from 'next'
import Providers from './providers'
import './globals.css'

export const metadata: Metadata = {
  title: 'Billing Calculator | Minimal & Elegant',
  description: 'Calculate and test billing scenarios with a beautiful interface',
  icons: {
    icon: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}): JSX.Element {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="font-kinfolk bg-kinfolk-beige-50 text-kinfolk-gray-900 antialiased">
        <Providers>
          {children}
        </Providers>
      </body>
    </html>
  )
}


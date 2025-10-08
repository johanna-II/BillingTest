/**
 * Providers Component - Client-side providers wrapper
 */

'use client'

import React from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { queryClient } from '@/lib/queryClient'
import { BillingProvider } from '@/contexts/BillingContext'

export default function Providers({ children }: { children: React.ReactNode }): JSX.Element {
  return (
    <QueryClientProvider client={queryClient}>
      <BillingProvider>
        {children}
      </BillingProvider>
    </QueryClientProvider>
  )
}



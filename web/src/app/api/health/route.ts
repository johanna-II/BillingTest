/**
 * Health Check Endpoint for Web App
 */

import { NextResponse } from 'next/server'

export async function GET() {
  return NextResponse.json({
    status: 'healthy',
    timestamp: new Date().toISOString(),
    service: 'billing-calculator-web',
  })
}



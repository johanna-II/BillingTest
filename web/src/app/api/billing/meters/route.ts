/**
 * Metering API Proxy
 * Proxies to /billing/meters
 */

import { NextRequest, NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const uuid = request.headers.get('uuid') || body.uuid

    const response = await fetch(`${API_BASE_URL}/billing/meters`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'uuid': uuid,
      },
      body: JSON.stringify(body),
    })

    const data = await response.json()

    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, uuid',
      },
    })
  } catch (error) {
    console.error('Metering error:', error)
    return NextResponse.json(
      {
        header: {
          isSuccessful: false,
          resultCode: '500',
          resultMessage: 'Failed to send metering data',
        },
        error: error instanceof Error ? error.message : 'Unknown error',
      },
      { status: 500 }
    )
  }
}

export async function OPTIONS() {
  return new NextResponse(null, {
    status: 200,
    headers: {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, uuid',
    },
  })
}



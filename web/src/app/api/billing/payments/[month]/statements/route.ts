/**
 * Statements API Proxy
 * Proxies to /billing/payments/<month>/statements
 */

import { NextRequest, NextResponse } from 'next/server'

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'

export async function GET(
  request: NextRequest,
  { params }: { params: { month: string } }
) {
  try {
    const { month } = params
    const { searchParams } = new URL(request.url)
    const uuid = searchParams.get('uuid') || request.headers.get('uuid')

    if (!uuid) {
      return NextResponse.json(
        {
          header: {
            isSuccessful: false,
            resultCode: '401',
            resultMessage: 'UUID is required',
          },
        },
        { status: 401 }
      )
    }

    const response = await fetch(
      `${API_BASE_URL}/billing/payments/${month}/statements?uuid=${uuid}`,
      {
        headers: {
          'uuid': uuid,
        },
      }
    )

    const data = await response.json()

    return NextResponse.json(data, {
      status: response.status,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, uuid',
      },
    })
  } catch (error) {
    console.error('Fetch statements error:', error)
    return NextResponse.json(
      {
        header: {
          isSuccessful: false,
          resultCode: '500',
          resultMessage: 'Failed to fetch statements',
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
      'Access-Control-Allow-Methods': 'GET, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, uuid',
    },
  })
}



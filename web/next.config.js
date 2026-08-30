/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export for Cloudflare Pages; standard build on Vercel
  ...(process.env.VERCEL ? {} : { output: 'export', trailingSlash: true }),
  images: {
    unoptimized: true, // Image optimization not available in static export
  },

  // Development only: Proxy /api requests to mock server
  async rewrites() {
    // Only in development (not in static export)
    if (process.env.NODE_ENV === 'development' && !process.env.NEXT_PUBLIC_API_URL?.includes('workers.dev')) {
      return [
        {
          source: '/api/:path*',
          destination: 'http://localhost:5000/:path*',
        },
      ]
    }
    return []
  },
}

module.exports = nextConfig

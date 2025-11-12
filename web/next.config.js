/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export', // Static site generation for Cloudflare Pages
  trailingSlash: true, // Better compatibility with static hosting
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

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Rewrites are handled by API routes for better CORS control
}

module.exports = nextConfig


/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'export', // Static site generation for Cloudflare Pages
  trailingSlash: true, // Better compatibility with static hosting
  images: {
    unoptimized: true, // Image optimization not available in static export
  },
}

module.exports = nextConfig

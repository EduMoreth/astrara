/** @type {import('next').NextConfig} */
const nextConfig = {
  // 'export' for Capacitor mobile builds, 'standalone' for Railway server deploy
  output: process.env.CAPACITOR_BUILD === 'true' ? 'export' : 'standalone',
  // Required for static export with dynamic routes
  ...(process.env.CAPACITOR_BUILD === 'true' && {
    images: { unoptimized: true },
  }),
}

module.exports = nextConfig

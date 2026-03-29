const fs = require('fs')

const isMobileBuild = fs.existsSync('.mobile-build')

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: isMobileBuild ? 'export' : 'standalone',
  ...(isMobileBuild && { images: { unoptimized: true } }),
}

module.exports = nextConfig

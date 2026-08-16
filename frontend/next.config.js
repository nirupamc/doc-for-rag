/** @type {import('next').NextConfig} */
module.exports = {
  reactStrictMode: false,
  experimental: {
    appDir: true,
  },
  images: {
    dangerouslyAllowSVG: true,
    contentSecurityPolicy: "default-src - 'self'; img-src - 'self' data: https:; style-src - 'self'; sandbox allow-scripts allow-same-origin",
  },
}
/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",   // needed for Docker — self-contained build
  reactStrictMode: false,
  typescript: {
    ignoreBuildErrors: true,  // type-check locally, not in Docker build
  },
  eslint: {
    ignoreDuringBuilds: true, // lint locally, not in Docker build
  },
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_GOOGLE_REVIEW_URL: process.env.NEXT_PUBLIC_GOOGLE_REVIEW_URL,
  },
};

module.exports = nextConfig;

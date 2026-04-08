/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",   // needed for Docker — self-contained build
  reactStrictMode: false,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    NEXT_PUBLIC_GOOGLE_REVIEW_URL: process.env.NEXT_PUBLIC_GOOGLE_REVIEW_URL,
  },
};

module.exports = nextConfig;

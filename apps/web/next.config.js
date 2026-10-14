/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  async rewrites() {
    const apiHost = process.env.API_HOST || "localhost";
    const apiPort = process.env.API_PORT || "8000";
    return [
      {
        source: "/api/:path*",
        destination: `http://${apiHost}:${apiPort}/api/:path*`,
      },
      {
        source: "/docs",
        destination: `http://${apiHost}:${apiPort}/docs`,
      },
      {
        source: "/openapi.json",
        destination: `http://${apiHost}:${apiPort}/openapi.json`,
      },
    ];
  },
};

module.exports = nextConfig;

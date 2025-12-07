/** @type {import('next').NextConfig} */
const backendUrl = process.env.FASTAPI_URL ?? "http://127.0.0.1:8000";

const nextConfig = {
    reactStrictMode: true,
    async rewrites() {
        return [
            {
                source: "/api/backend/:path*",
                destination: `${backendUrl}/:path*`
            }
        ];
    }
};

export default nextConfig;

/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',

    typescript: {
        ignoreBuildErrors: true,
    },

    eslint: {
        ignoreDuringBuilds: true,
    },

    experimental: {
        serverActions: {
            bodySizeLimit: '2mb',
        },
    },

    images: {
        remotePatterns: [
            {
                protocol: 'https',
                hostname: '*.supabase.co',
            },
            {
                protocol: 'http',
                hostname: 'localhost',
            },
            {
                protocol: 'https',
                hostname: 'profile.line-scdn.net',
            },
        ],
    },

    env: {
        NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
        NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL,
    },

    async rewrites() {
        return []
    },

    async headers() {
        return [
            {
                source: '/:path*',
                headers: [
                    {
                        key: 'X-Frame-Options',
                        value: 'DENY',
                    },
                    {
                        key: 'X-Content-Type-Options',
                        value: 'nosniff',
                    },
                    {
                        key: 'Referrer-Policy',
                        value: 'origin-when-cross-origin',
                    },
                ],
            },
        ]
    },
}

module.exports = nextConfig

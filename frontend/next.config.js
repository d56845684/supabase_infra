// ==========================================
// next.config.js
// ==========================================

/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone', // 用於 Docker 部署

    experimental: {
        serverActions: {
            bodySizeLimit: '2mb',
        },
    },

    // 圖片優化配置
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
        ],
    },

    // 環境變數
    env: {
        NEXT_PUBLIC_SUPABASE_URL: process.env.NEXT_PUBLIC_SUPABASE_URL,
        NEXT_PUBLIC_SUPABASE_ANON_KEY: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY,
    },

    // 重寫規則（如果需要代理 API）
    async rewrites() {
        return [
            // 可以在這裡添加 API 代理規則
        ]
    },

    // Headers
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

// ==========================================
// tailwind.config.js
// ==========================================
/*
/** @type {import('tailwindcss').Config} *\/
module.exports = {
  content: [
    './src/pages/**/*.{ js, ts, jsx, tsx, mdx } ',
'./src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
theme: {
    extend: {
        colors: {
            primary: {
                50: '#eff6ff',
                    100: '#dbeafe',
                        200: '#bfdbfe',
                            300: '#93c5fd',
                                400: '#60a5fa',
                                    500: '#3b82f6',
                                        600: '#2563eb',
                                            700: '#1d4ed8',
                                                800: '#1e40af',
                                                    900: '#1e3a8a',
        },
        },
    },
},
plugins: [],
}
*/

// ==========================================
// tsconfig.json
// ==========================================
/*
{
  "compilerOptions": {
    "target": "es5",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["next-env.d.ts", "**/*.ts", " **/*.tsx", ".next/types/**/*.ts"],
"exclude": ["node_modules"]
}
*/

// ==========================================
// middleware.ts (放在 src/ 根目錄)
// ==========================================
/*
import { NextResponse, type NextRequest } from 'next/server'
import { updateSession } from '@/lib/supabase/middleware'

export async function middleware(request: NextRequest) {
  return await updateSession(request)
}

export const config = {
  matcher: [
    // 排除靜態資源和 API
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
*/
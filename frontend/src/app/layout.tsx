import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '教學管理系統',
  description: 'Education Management System',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-TW">
      <body className="antialiased">{children}</body>
    </html>
  )
}

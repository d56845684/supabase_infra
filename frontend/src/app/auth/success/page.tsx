'use client'

import { Suspense } from 'react'
import { useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { CheckCircle } from 'lucide-react'

function AuthSuccessContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [countdown, setCountdown] = useState(3)

  const isNewUser = searchParams.get('new_user') === 'true'
  const channel = searchParams.get('channel') || 'student'

  useEffect(() => {
    const timer = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(timer)
          router.push('/profile')
          return 0
        }
        return prev - 1
      })
    }, 1000)

    return () => clearInterval(timer)
  }, [router])

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="card text-center max-w-md">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-green-100 flex items-center justify-center">
          <CheckCircle className="w-10 h-10 text-green-600" />
        </div>

        <h1 className="text-2xl font-bold text-green-600 mb-2">
          {isNewUser ? '註冊成功！' : '綁定成功！'}
        </h1>

        <p className="text-gray-600 mb-4">
          {isNewUser
            ? '您的 Line 帳號已成功註冊'
            : '您的 Line 帳號已成功綁定'}
        </p>

        <p className="text-sm text-gray-400">
          {countdown} 秒後自動跳轉...
        </p>

        <button
          onClick={() => router.push('/profile')}
          className="btn-primary mt-4"
        >
          立即前往個人頁面
        </button>
      </div>
    </div>
  )
}

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="card text-center max-w-md">
        <div className="animate-spin w-8 h-8 border-4 border-line-green border-t-transparent rounded-full mx-auto"></div>
        <p className="mt-4 text-gray-600">載入中...</p>
      </div>
    </div>
  )
}

export default function AuthSuccessPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <AuthSuccessContent />
    </Suspense>
  )
}

'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useRouter } from 'next/navigation'
import { XCircle } from 'lucide-react'

function AuthErrorContent() {
  const router = useRouter()
  const searchParams = useSearchParams()

  const error = searchParams.get('error') || 'unknown_error'
  const description = searchParams.get('description') || ''

  const errorMessages: Record<string, string> = {
    missing_params: '缺少必要參數',
    invalid_state: '驗證狀態無效，請重新嘗試',
    line_auth_failed: 'Line 認證失敗',
    line_already_bound: 'Line 帳號已被綁定',
    access_denied: '使用者拒絕授權',
    unknown_error: '發生未知錯誤',
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4">
      <div className="card text-center max-w-md">
        <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-red-100 flex items-center justify-center">
          <XCircle className="w-10 h-10 text-red-600" />
        </div>

        <h1 className="text-2xl font-bold text-red-600 mb-2">認證失敗</h1>

        <p className="text-gray-600 mb-2">
          {errorMessages[error] || errorMessages.unknown_error}
        </p>

        {description && (
          <p className="text-sm text-gray-400 mb-4 break-words">
            {decodeURIComponent(description)}
          </p>
        )}

        <div className="flex gap-3 justify-center mt-4">
          <button
            onClick={() => router.push('/login')}
            className="btn-secondary"
          >
            返回登入
          </button>
          <button
            onClick={() => router.push('/profile')}
            className="btn-primary"
          >
            前往個人頁面
          </button>
        </div>
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

export default function AuthErrorPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <AuthErrorContent />
    </Suspense>
  )
}

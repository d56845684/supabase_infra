'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/hooks/useAuth'
import { useLine } from '@/lib/hooks/useLine'
import { LogOut, User, Link as LinkIcon, Unlink } from 'lucide-react'

export default function ProfilePage() {
  const router = useRouter()
  const { user, profile, loading: authLoading, signOut } = useAuth()
  const { bindings, loading: lineLoading, startBinding, unbind, isBound, fetchBindings } = useLine()

  useEffect(() => {
    if (!authLoading && !user) {
      router.push('/login')
    }
  }, [authLoading, user, router])

  const handleSignOut = async () => {
    await signOut()
    router.push('/login')
  }

  const handleBindLine = async () => {
    await startBinding()
  }

  const handleUnbindLine = async (channel: string) => {
    if (confirm('確定要解除 Line 綁定嗎？')) {
      await unbind(channel)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  const roleLabels: Record<string, string> = {
    admin: '管理員',
    teacher: '老師',
    student: '學生',
    employee: '員工',
  }

  const channelLabels: Record<string, string> = {
    student: '學生',
    teacher: '老師',
    employee: '員工',
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      <div className="max-w-2xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">個人設定</h1>
          <button
            onClick={handleSignOut}
            className="btn-secondary flex items-center gap-2"
          >
            <LogOut className="w-4 h-4" />
            登出
          </button>
        </div>

        {/* Profile Card */}
        <div className="card">
          <div className="flex items-center gap-4 mb-6">
            <div className="w-16 h-16 rounded-full bg-blue-100 flex items-center justify-center">
              {profile?.avatar_url ? (
                <img
                  src={profile.avatar_url}
                  alt="Avatar"
                  className="w-16 h-16 rounded-full object-cover"
                />
              ) : (
                <User className="w-8 h-8 text-blue-600" />
              )}
            </div>
            <div>
              <h2 className="text-xl font-semibold">
                {profile?.full_name || user.email}
              </h2>
              <p className="text-gray-500">{user.email}</p>
              {profile?.role && (
                <span className="inline-block mt-1 px-2 py-0.5 bg-blue-100 text-blue-700 text-sm rounded">
                  {roleLabels[profile.role] || profile.role}
                </span>
              )}
            </div>
          </div>

          <div className="border-t pt-4">
            <h3 className="font-medium text-gray-700 mb-2">帳號資訊</h3>
            <dl className="space-y-2 text-sm">
              <div className="flex">
                <dt className="w-24 text-gray-500">Email</dt>
                <dd>{user.email}</dd>
              </div>
              {profile?.phone && (
                <div className="flex">
                  <dt className="w-24 text-gray-500">電話</dt>
                  <dd>{profile.phone}</dd>
                </div>
              )}
              <div className="flex">
                <dt className="w-24 text-gray-500">User ID</dt>
                <dd className="font-mono text-xs text-gray-400">{user.id}</dd>
              </div>
            </dl>
          </div>
        </div>

        {/* Line Binding Card */}
        <div className="card">
          <div className="flex items-center gap-2 mb-4">
            <svg className="w-6 h-6 text-[#06C755]" viewBox="0 0 24 24" fill="currentColor">
              <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63h2.386c.349 0 .63.285.63.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/>
            </svg>
            <h3 className="text-lg font-semibold">Line 帳號綁定</h3>
          </div>

          {lineLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-[#06C755]"></div>
            </div>
          ) : bindings.length > 0 && bindings.some(b => b.is_bound) ? (
            <div className="space-y-4">
              {bindings.filter(b => b.is_bound).map((binding) => (
                <div
                  key={binding.channel_type}
                  className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200"
                >
                  <div className="flex items-center gap-3">
                    {binding.line_picture_url ? (
                      <img
                        src={binding.line_picture_url}
                        alt="Line Avatar"
                        className="w-12 h-12 rounded-full"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-[#06C755] flex items-center justify-center">
                        <svg className="w-6 h-6 text-white" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M19.365 9.863c.349 0 .63.285.63.631 0 .345-.281.63-.63.63H17.61v1.125h1.755c.349 0 .63.283.63.63 0 .344-.281.629-.63.629h-2.386c-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63h2.386c.349 0 .63.285.63.63 0 .349-.281.63-.63.63H17.61v1.125h1.755zm-3.855 3.016c0 .27-.174.51-.432.596-.064.021-.133.031-.199.031-.211 0-.391-.09-.51-.25l-2.443-3.317v2.94c0 .344-.279.629-.631.629-.346 0-.626-.285-.626-.629V8.108c0-.27.173-.51.43-.595.06-.023.136-.033.194-.033.195 0 .375.104.495.254l2.462 3.33V8.108c0-.345.282-.63.63-.63.345 0 .63.285.63.63v4.771zm-5.741 0c0 .344-.282.629-.631.629-.345 0-.627-.285-.627-.629V8.108c0-.345.282-.63.627-.63.349 0 .631.285.631.63v4.771zm-2.466.629H4.917c-.345 0-.63-.285-.63-.629V8.108c0-.345.285-.63.63-.63.348 0 .63.285.63.63v4.141h1.756c.348 0 .629.283.629.63 0 .344-.282.629-.629.629M24 10.314C24 4.943 18.615.572 12 .572S0 4.943 0 10.314c0 4.811 4.27 8.842 10.035 9.608.391.082.923.258 1.058.59.12.301.079.766.038 1.08l-.164 1.02c-.045.301-.24 1.186 1.049.645 1.291-.539 6.916-4.078 9.436-6.975C23.176 14.393 24 12.458 24 10.314"/>
                        </svg>
                      </div>
                    )}
                    <div>
                      <p className="font-medium">{binding.line_display_name}</p>
                      <p className="text-sm text-gray-500">
                        {channelLabels[binding.channel_type] || binding.channel_type} 頻道
                      </p>
                      {binding.bound_at && (
                        <p className="text-xs text-gray-400">
                          綁定於 {new Date(binding.bound_at).toLocaleDateString('zh-TW')}
                        </p>
                      )}
                    </div>
                  </div>
                  <button
                    onClick={() => handleUnbindLine(binding.channel_type)}
                    className="btn-danger flex items-center gap-1 text-sm py-1.5 px-3"
                  >
                    <Unlink className="w-4 h-4" />
                    解除綁定
                  </button>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
                <LinkIcon className="w-8 h-8 text-gray-400" />
              </div>
              <p className="text-gray-500 mb-4">尚未綁定 Line 帳號</p>
              <p className="text-sm text-gray-400 mb-6">
                綁定後可接收課程通知、預約提醒等訊息
              </p>
              <button
                onClick={handleBindLine}
                className="btn-line flex items-center justify-center gap-2 mx-auto"
              >
                <LinkIcon className="w-4 h-4" />
                綁定 Line 帳號
              </button>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="card bg-blue-50 border border-blue-200">
          <h3 className="font-medium text-blue-800 mb-2">關於 Line 綁定</h3>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• 綁定後可透過 Line 接收系統通知</li>
            <li>• 包含課程提醒、預約確認等重要訊息</li>
            <li>• 您可以隨時解除綁定</li>
          </ul>
        </div>
      </div>
    </div>
  )
}

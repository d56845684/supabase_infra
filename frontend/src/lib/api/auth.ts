// Use backend API for authentication instead of direct Supabase calls
// This avoids CORS issues with the Supabase client

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

interface AuthResponse {
    success: boolean
    message: string
    user?: {
        id: string
        email: string
        role: string
        email_confirmed: boolean
    }
    tokens?: {
        access_token: string
        refresh_token: string
        token_type: string
        expires_in: number
    }
}

interface UserProfile {
    id: string
    role: string
    full_name: string
    email: string
    phone?: string
    avatar_url?: string
}

export const authApi = {
    async signIn(email: string, password: string) {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify({ email, password }),
            })

            const result: AuthResponse = await response.json()

            if (!response.ok || !result.success) {
                return {
                    data: null,
                    error: { message: result.message || '登入失敗' }
                }
            }

            // Store tokens in localStorage for the app to use
            if (result.tokens) {
                localStorage.setItem('access_token', result.tokens.access_token)
                localStorage.setItem('refresh_token', result.tokens.refresh_token)
            }

            return {
                data: {
                    user: result.user,
                    session: result.tokens
                },
                error: null
            }
        } catch (err) {
            return {
                data: null,
                error: { message: '網路錯誤，請稍後再試' }
            }
        }
    },

    async signOut() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
                method: 'POST',
                credentials: 'include',
            })

            // Clear local storage
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')

            if (!response.ok) {
                return { error: { message: '登出失敗' } }
            }

            return { error: null }
        } catch (err) {
            // Still clear storage on error
            localStorage.removeItem('access_token')
            localStorage.removeItem('refresh_token')
            return { error: null }
        }
    },

    async getCurrentUser() {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                method: 'GET',
                credentials: 'include',
            })

            if (!response.ok) {
                return { user: null, error: { message: '未登入' } }
            }

            const result = await response.json()
            return {
                user: result.user || result,
                error: null
            }
        } catch (err) {
            return { user: null, error: { message: '無法取得用戶資訊' } }
        }
    },

    async getUserProfile(userId: string): Promise<{ data: UserProfile | null, error: any }> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
                method: 'GET',
                credentials: 'include',
            })

            if (!response.ok) {
                return { data: null, error: { message: '無法取得用戶資料' } }
            }

            const result = await response.json()

            // Map backend response to UserProfile format
            const profile: UserProfile = {
                id: result.user?.id || userId,
                role: result.user?.role || 'student',
                full_name: result.user?.name || result.user?.email || '',
                email: result.user?.email || '',
                phone: result.user?.phone,
                avatar_url: result.user?.avatar_url,
            }

            return { data: profile, error: null }
        } catch (err) {
            return { data: null, error: { message: '無法取得用戶資料' } }
        }
    },
}

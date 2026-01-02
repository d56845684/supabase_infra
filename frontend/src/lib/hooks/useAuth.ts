// ==========================================
// src/lib/hooks/useAuth.ts
// ==========================================
import { useState, useEffect, useCallback } from 'react'
import { getSupabaseClient } from '../supabase/client'
import { authApi } from '../api/auth'
import type { User } from '@supabase/supabase-js'

interface UserProfile {
    id: string
    role: 'admin' | 'teacher' | 'student'
    full_name: string
    email: string
    phone?: string
    avatar_url?: string
}

export function useAuth() {
    const [user, setUser] = useState<User | null>(null)
    const [profile, setProfile] = useState<UserProfile | null>(null)
    const [loading, setLoading] = useState(true)

    const fetchProfile = useCallback(async (userId: string) => {
        const { data } = await authApi.getUserProfile(userId)
        if (data) {
            setProfile(data as UserProfile)
        }
    }, [])

    useEffect(() => {
        const supabase = getSupabaseClient()

        // 初始檢查
        supabase.auth.getUser().then(({ data: { user } }) => {
            setUser(user)
            if (user) {
                fetchProfile(user.id)
            }
            setLoading(false)
        })

        // 監聽 auth 變化
        const { data: { subscription } } = supabase.auth.onAuthStateChange(
            async (event, session) => {
                setUser(session?.user ?? null)
                if (session?.user) {
                    await fetchProfile(session.user.id)
                } else {
                    setProfile(null)
                }
                setLoading(false)
            }
        )

        return () => subscription.unsubscribe()
    }, [fetchProfile])

    const signIn = async (email: string, password: string) => {
        setLoading(true)
        const result = await authApi.signIn(email, password)
        setLoading(false)
        return result
    }

    const signOut = async () => {
        setLoading(true)
        const result = await authApi.signOut()
        setUser(null)
        setProfile(null)
        setLoading(false)
        return result
    }

    return {
        user,
        profile,
        loading,
        signIn,
        signOut,
        isAdmin: profile?.role === 'admin',
        isTeacher: profile?.role === 'teacher',
        isStudent: profile?.role === 'student',
    }
}

// ==========================================
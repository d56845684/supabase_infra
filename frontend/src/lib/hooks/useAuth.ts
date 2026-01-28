// useAuth hook - uses backend API for authentication
import { useState, useEffect, useCallback } from 'react'
import { authApi } from '../api/auth'

interface User {
    id: string
    email: string
    role?: string
}

interface UserProfile {
    id: string
    role: 'admin' | 'teacher' | 'student' | 'employee'
    full_name: string
    email: string
    phone?: string
    avatar_url?: string
}

export function useAuth() {
    const [user, setUser] = useState<User | null>(null)
    const [profile, setProfile] = useState<UserProfile | null>(null)
    const [loading, setLoading] = useState(true)

    const fetchCurrentUser = useCallback(async () => {
        try {
            const { user: currentUser, error } = await authApi.getCurrentUser()
            if (error || !currentUser) {
                setUser(null)
                setProfile(null)
                return
            }

            setUser(currentUser)

            // Fetch profile
            const { data: profileData } = await authApi.getUserProfile(currentUser.id)
            if (profileData) {
                setProfile(profileData)
            }
        } catch (err) {
            setUser(null)
            setProfile(null)
        }
    }, [])

    useEffect(() => {
        // Check if user is logged in on mount
        fetchCurrentUser().finally(() => {
            setLoading(false)
        })
    }, [fetchCurrentUser])

    const signIn = async (email: string, password: string) => {
        setLoading(true)
        const result = await authApi.signIn(email, password)

        if (result.data?.user) {
            setUser(result.data.user as User)
            // Fetch profile after login
            const { data: profileData } = await authApi.getUserProfile(result.data.user.id)
            if (profileData) {
                setProfile(profileData)
            }
        }

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
        refreshUser: fetchCurrentUser,
        isAdmin: profile?.role === 'admin',
        isTeacher: profile?.role === 'teacher',
        isStudent: profile?.role === 'student',
        isEmployee: profile?.role === 'employee',
    }
}

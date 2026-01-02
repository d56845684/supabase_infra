import { getSupabaseClient } from '../supabase/client'

export const authApi = {
    async signIn(email: string, password: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.auth.signInWithPassword({
            email,
            password,
        })
        return { data, error }
    },

    async signUp(email: string, password: string, metadata: { full_name: string; phone?: string }) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.auth.signUp({
            email,
            password,
            options: {
                data: metadata,
            },
        })
        return { data, error }
    },

    async signOut() {
        const supabase = getSupabaseClient()
        const { error } = await supabase.auth.signOut()
        return { error }
    },

    async getCurrentUser() {
        const supabase = getSupabaseClient()
        const { data: { user }, error } = await supabase.auth.getUser()
        return { user, error }
    },

    async getUserProfile(userId: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('user_profiles')
            .select('*')
            .eq('id', userId)
            .single()
        return { data, error }
    },
}

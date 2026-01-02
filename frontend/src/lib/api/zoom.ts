// src/lib/api/zoom.ts
// ==========================================
import { getSupabaseClient } from '../supabase/client'

export const zoomApi = {
    async getAccounts() {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('zoom_accounts')
            .select('*')
            .is('deleted_at', null)
            .order('created_at', { ascending: false })
        return { data, error }
    },

    async getAvailableAccount() {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('zoom_accounts')
            .select('*')
            .eq('is_active', true)
            .is('deleted_at', null)
            .limit(1)
            .single()
        return { data, error }
    },
}
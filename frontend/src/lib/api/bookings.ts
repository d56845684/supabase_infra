// ==========================================
// src/lib/api/bookings.ts
// ==========================================
import { getSupabaseClient } from '../supabase/client'

export const bookingsApi = {
    async getAll(includeDeleted = false) {
        const supabase = getSupabaseClient()

        if (includeDeleted) {
            const { data, error } = await supabase
                .from('bookings')
                .select(`
          *,
          students:student_id (id, user_profiles (*)),
          teachers:teacher_id (id, user_profiles (*))
        `)
                .order('scheduled_start', { ascending: false })
            return { data, error }
        }

        const { data, error } = await supabase
            .from('v_active_bookings')
            .select('*')
            .order('scheduled_start', { ascending: false })
        return { data, error }
    },

    async create(booking: {
        student_id: string
        teacher_id: string
        scheduled_start: string
        scheduled_end: string
        contract_id?: string
        zoom_account_id?: string
    }) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('bookings')
            .insert(booking)
            .select()
            .single()
        return { data, error }
    },

    async updateStatus(id: string, status: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('bookings')
            .update({ status, updated_at: new Date().toISOString() })
            .eq('id', id)
            .select()
            .single()
        return { data, error }
    },

    async softDelete(id: string) {
        const supabase = getSupabaseClient()
        const { data: { user } } = await supabase.auth.getUser()
        const { data, error } = await supabase
            .from('bookings')
            .update({
                deleted_at: new Date().toISOString(),
                deleted_by: user?.id
            })
            .eq('id', id)
            .select()
            .single()
        return { data, error }
    },

    async restore(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('bookings')
            .update({ deleted_at: null, deleted_by: null })
            .eq('id', id)
            .select()
            .single()
        return { data, error }
    },
}

// ==========================================

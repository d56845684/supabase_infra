import { getSupabaseClient } from '../supabase/client'

export const teachersApi = {
    async getAll(includeDeleted = false) {
        const supabase = getSupabaseClient()

        if (includeDeleted) {
            const { data, error } = await supabase
                .from('teachers')
                .select(`*, user_profiles (*)`)
                .order('created_at', { ascending: false })
            return { data, error }
        }

        const { data, error } = await supabase
            .from('v_active_teachers')
            .select('*')
            .order('created_at', { ascending: false })
        return { data, error }
    },

    async getById(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('teachers')
            .select(`
        *,
        user_profiles (*),
        teacher_contracts (*),
        teacher_payroll (*),
        bookings (*)
      `)
            .eq('id', id)
            .single()
        return { data, error }
    },

    async updateStatus(id: string, status: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('teachers')
            .update({ teacher_status: status, updated_at: new Date().toISOString() })
            .eq('id', id)
            .select()
            .single()
        return { data, error }
    },

    async softDelete(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.rpc('soft_delete_teacher', {
            teacher_id: id,
        })
        return { data, error }
    },

    async restore(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.rpc('restore_teacher', {
            teacher_id: id,
        })
        return { data, error }
    },
}

// ==========================================

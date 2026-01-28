// src/lib/api/students.ts
import { getSupabaseClient } from '../supabase/client'

export const studentsApi = {
    async getAll(includeDeleted = false) {
        const supabase = getSupabaseClient()

        if (includeDeleted) {
            const { data, error } = await supabase
                .from('students')
                .select(`
          *,
          user_profiles (*)
        `)
                .order('created_at', { ascending: false })
            return { data, error }
        }

        const { data, error } = await supabase
            .from('v_active_students' as any)
            .select('*')
            .order('created_at', { ascending: false })
        return { data, error }
    },

    async getById(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('students')
            .select(`
        *,
        user_profiles (*),
        student_contracts (*),
        bookings (*)
      `)
            .eq('id', id)
            .single()
        return { data, error }
    },

    async updateStatus(id: string, status: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('students')
            .update({ student_status: status, updated_at: new Date().toISOString() } as any)
            .eq('id', id)
            .select()
            .single()
        return { data, error }
    },

    async softDelete(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.rpc('soft_delete_student' as any, {
            student_id: id,
        })
        return { data, error }
    },

    async restore(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.rpc('restore_student' as any, {
            student_id: id,
        })
        return { data, error }
    },
}

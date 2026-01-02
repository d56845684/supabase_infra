// ==========================================
// src/lib/api/students.ts
// ==========================================
import { getSupabaseClient } from '../supabase/client'

export const studentsApi = {
    async getAll(includeDeleted = false) {
        const supabase = getSupabaseClient()
        let query = supabase
            .from('v_active_students')
            .select('*')
            .order('created_at', { ascending: false })

        // v_active_students 已經排除 deleted_at
        // 如果要包含已刪除的，需要查原表
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

        const { data, error } = await query
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
            .update({ student_status: status, updated_at: new Date().toISOString() })
            .eq('id', id)
            .select()
            .single()
        return { data, error }
    },

    async softDelete(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.rpc('soft_delete_student', {
            student_id: id,
        })
        return { data, error }
    },

    async restore(id: string) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase.rpc('restore_student', {
            student_id: id,
        })
        return { data, error }
    },
}

// ==========================================
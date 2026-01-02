// ==========================================
// src/lib/api/contracts.ts
// ==========================================
import { getSupabaseClient } from '../supabase/client'

export const contractsApi = {
    async getStudentContracts(studentId?: string) {
        const supabase = getSupabaseClient()
        let query = supabase
            .from('student_contracts')
            .select(`
        *,
        students:student_id (id, user_profiles (*))
      `)
            .is('deleted_at', null)
            .order('created_at', { ascending: false })

        if (studentId) {
            query = query.eq('student_id', studentId)
        }

        const { data, error } = await query
        return { data, error }
    },

    async getTeacherContracts(teacherId?: string) {
        const supabase = getSupabaseClient()
        let query = supabase
            .from('teacher_contracts')
            .select(`
        *,
        teachers:teacher_id (id, user_profiles (*))
      `)
            .is('deleted_at', null)
            .order('created_at', { ascending: false })

        if (teacherId) {
            query = query.eq('teacher_id', teacherId)
        }

        const { data, error } = await query
        return { data, error }
    },

    async createStudentContract(contract: {
        student_id: string
        contract_number: string
        total_lessons: number
        remaining_lessons: number
        price_per_lesson: number
        total_amount: number
        start_date: string
        end_date: string
    }) {
        const supabase = getSupabaseClient()
        const { data, error } = await supabase
            .from('student_contracts')
            .insert(contract)
            .select()
            .single()
        return { data, error }
    },
}

// ==========================================
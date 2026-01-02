// ==========================================
// src/lib/hooks/useStudents.ts
// ==========================================
import { useState, useEffect, useCallback } from 'react'
import { studentsApi } from '../api/students'

export function useStudents(includeDeleted = false) {
    const [students, setStudents] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchStudents = useCallback(async () => {
        setLoading(true)
        const { data, error } = await studentsApi.getAll(includeDeleted)
        if (error) {
            setError(error.message)
        } else {
            setStudents(data || [])
        }
        setLoading(false)
    }, [includeDeleted])

    useEffect(() => {
        fetchStudents()
    }, [fetchStudents])

    const updateStatus = async (id: string, status: string) => {
        const { error } = await studentsApi.updateStatus(id, status)
        if (!error) {
            await fetchStudents()
        }
        return { error }
    }

    const softDelete = async (id: string) => {
        const { error } = await studentsApi.softDelete(id)
        if (!error) {
            await fetchStudents()
        }
        return { error }
    }

    const restore = async (id: string) => {
        const { error } = await studentsApi.restore(id)
        if (!error) {
            await fetchStudents()
        }
        return { error }
    }

    return {
        students,
        loading,
        error,
        refresh: fetchStudents,
        updateStatus,
        softDelete,
        restore,
    }
}

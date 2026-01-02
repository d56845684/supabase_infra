// src/lib/hooks/useTeachers.ts
// ==========================================
import { useState, useEffect, useCallback } from 'react'
import { teachersApi } from '../api/teachers'

export function useTeachers(includeDeleted = false) {
    const [teachers, setTeachers] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchTeachers = useCallback(async () => {
        setLoading(true)
        const { data, error } = await teachersApi.getAll(includeDeleted)
        if (error) {
            setError(error.message)
        } else {
            setTeachers(data || [])
        }
        setLoading(false)
    }, [includeDeleted])

    useEffect(() => {
        fetchTeachers()
    }, [fetchTeachers])

    const updateStatus = async (id: string, status: string) => {
        const { error } = await teachersApi.updateStatus(id, status)
        if (!error) {
            await fetchTeachers()
        }
        return { error }
    }

    const softDelete = async (id: string) => {
        const { error } = await teachersApi.softDelete(id)
        if (!error) {
            await fetchTeachers()
        }
        return { error }
    }

    const restore = async (id: string) => {
        const { error } = await teachersApi.restore(id)
        if (!error) {
            await fetchTeachers()
        }
        return { error }
    }

    return {
        teachers,
        loading,
        error,
        refresh: fetchTeachers,
        updateStatus,
        softDelete,
        restore,
    }
}
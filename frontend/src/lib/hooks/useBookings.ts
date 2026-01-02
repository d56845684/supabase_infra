// src/lib/hooks/useBookings.ts
// ==========================================
import { useState, useEffect, useCallback } from 'react'
import { bookingsApi } from '../api/bookings'

export function useBookings(includeDeleted = false) {
    const [bookings, setBookings] = useState<any[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    const fetchBookings = useCallback(async () => {
        setLoading(true)
        const { data, error } = await bookingsApi.getAll(includeDeleted)
        if (error) {
            setError(error.message)
        } else {
            setBookings(data || [])
        }
        setLoading(false)
    }, [includeDeleted])

    useEffect(() => {
        fetchBookings()
    }, [fetchBookings])

    const create = async (booking: Parameters<typeof bookingsApi.create>[0]) => {
        const { data, error } = await bookingsApi.create(booking)
        if (!error) {
            await fetchBookings()
        }
        return { data, error }
    }

    const updateStatus = async (id: string, status: string) => {
        const { error } = await bookingsApi.updateStatus(id, status)
        if (!error) {
            await fetchBookings()
        }
        return { error }
    }

    const softDelete = async (id: string) => {
        const { error } = await bookingsApi.softDelete(id)
        if (!error) {
            await fetchBookings()
        }
        return { error }
    }

    const restore = async (id: string) => {
        const { error } = await bookingsApi.restore(id)
        if (!error) {
            await fetchBookings()
        }
        return { error }
    }

    return {
        bookings,
        loading,
        error,
        refresh: fetchBookings,
        create,
        updateStatus,
        softDelete,
        restore,
    }
}

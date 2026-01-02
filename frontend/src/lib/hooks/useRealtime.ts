// src/lib/hooks/useRealtime.ts
// ==========================================
import { useEffect } from 'react'
import { getSupabaseClient } from '../supabase/client'

export function useRealtime(
    table: string,
    onInsert?: (payload: any) => void,
    onUpdate?: (payload: any) => void,
    onDelete?: (payload: any) => void
) {
    useEffect(() => {
        const supabase = getSupabaseClient()

        const channel = supabase
            .channel(`${table}_changes`)
            .on(
                'postgres_changes',
                { event: 'INSERT', schema: 'public', table },
                (payload) => onInsert?.(payload)
            )
            .on(
                'postgres_changes',
                { event: 'UPDATE', schema: 'public', table },
                (payload) => onUpdate?.(payload)
            )
            .on(
                'postgres_changes',
                { event: 'DELETE', schema: 'public', table },
                (payload) => onDelete?.(payload)
            )
            .subscribe()

        return () => {
            supabase.removeChannel(channel)
        }
    }, [table, onInsert, onUpdate, onDelete])
}
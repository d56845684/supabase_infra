/**
 * Line 綁定 Hook
 */
import { useState, useEffect, useCallback } from 'react'
import { lineApi, LineBindingStatus } from '../api/line'

export function useLine() {
  const [bindings, setBindings] = useState<LineBindingStatus[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchBindings = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await lineApi.getAllBindings()
      setBindings(response.bindings)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch bindings')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchBindings()
  }, [fetchBindings])

  const startBinding = async (channel?: string) => {
    try {
      setError(null)
      const response = await lineApi.getBindUrl(channel)

      if (response.data?.is_bound) {
        // Already bound
        return { success: false, message: response.message, alreadyBound: true }
      }

      if (response.data?.bind_url) {
        // Redirect to Line authorization
        window.location.href = response.data.bind_url
        return { success: true, message: 'Redirecting to Line...' }
      }

      return { success: false, message: 'Failed to get bind URL' }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to start binding'
      setError(message)
      return { success: false, message }
    }
  }

  const unbind = async (channel?: string) => {
    try {
      setError(null)
      const response = await lineApi.unbind(channel)
      if (response.success) {
        // Refresh bindings
        await fetchBindings()
      }
      return response
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to unbind'
      setError(message)
      return { success: false, message }
    }
  }

  const getBinding = (channel: string) => {
    return bindings.find(b => b.channel_type === channel && b.is_bound)
  }

  const isBound = (channel?: string) => {
    if (channel) {
      return bindings.some(b => b.channel_type === channel && b.is_bound)
    }
    return bindings.some(b => b.is_bound)
  }

  return {
    bindings,
    loading,
    error,
    fetchBindings,
    startBinding,
    unbind,
    getBinding,
    isBound,
  }
}

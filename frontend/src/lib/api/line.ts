/**
 * Line 綁定 API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export interface LineBindingStatus {
  is_bound: boolean
  channel_type: string
  line_display_name?: string
  line_picture_url?: string
  bound_at?: string
  bind_url?: string
}

export interface LineBindingResponse {
  success: boolean
  message: string
  data?: LineBindingStatus
}

export interface LineBindingsListResponse {
  success: boolean
  message: string
  bindings: LineBindingStatus[]
}

export interface LineLoginUrlResponse {
  url: string
  state: string
  channel_type: string
}

export const lineApi = {
  /**
   * 取得 Line 登入 URL（新用戶註冊用）
   */
  async getLoginUrl(channel: string = 'student'): Promise<LineLoginUrlResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/auth/line/login?channel=${channel}`,
      {
        method: 'GET',
        credentials: 'include',
      }
    )

    if (!response.ok) {
      throw new Error('Failed to get Line login URL')
    }

    return response.json()
  },

  /**
   * 取得 Line 綁定 URL（已登入用戶綁定用）
   */
  async getBindUrl(channel?: string): Promise<LineBindingResponse> {
    const params = channel ? `?channel=${channel}` : ''
    const response = await fetch(
      `${API_BASE_URL}/api/v1/auth/line/bind${params}`,
      {
        method: 'POST',
        credentials: 'include',
      }
    )

    if (!response.ok) {
      const error = await response.json()
      throw new Error(error.detail || 'Failed to get bind URL')
    }

    return response.json()
  },

  /**
   * 取得單一頻道的 Line 綁定狀態
   */
  async getBindingStatus(channel?: string): Promise<LineBindingResponse> {
    const params = channel ? `?channel=${channel}` : ''
    const response = await fetch(
      `${API_BASE_URL}/api/v1/auth/line/status${params}`,
      {
        method: 'GET',
        credentials: 'include',
      }
    )

    if (!response.ok) {
      throw new Error('Failed to get binding status')
    }

    return response.json()
  },

  /**
   * 取得所有頻道的 Line 綁定狀態
   */
  async getAllBindings(): Promise<LineBindingsListResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/auth/line/bindings`,
      {
        method: 'GET',
        credentials: 'include',
      }
    )

    if (!response.ok) {
      throw new Error('Failed to get bindings')
    }

    return response.json()
  },

  /**
   * 解除 Line 綁定
   */
  async unbind(channel?: string): Promise<{ success: boolean; message: string }> {
    const params = channel ? `?channel=${channel}` : ''
    const response = await fetch(
      `${API_BASE_URL}/api/v1/auth/line/unbind${params}`,
      {
        method: 'DELETE',
        credentials: 'include',
      }
    )

    if (!response.ok) {
      throw new Error('Failed to unbind')
    }

    return response.json()
  },
}

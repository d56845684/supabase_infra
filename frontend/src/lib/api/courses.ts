const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001'

export interface Course {
    id: string
    course_code: string
    course_name: string
    description?: string
    duration_minutes: number
    is_active: boolean
    created_at?: string
    updated_at?: string
}

export interface CourseListResponse {
    success: boolean
    data: Course[]
    total: number
    page: number
    per_page: number
    total_pages: number
}

export interface CourseResponse {
    success: boolean
    message: string
    data?: Course
}

export interface CreateCourseData {
    course_code: string
    course_name: string
    description?: string
    duration_minutes?: number
    is_active?: boolean
}

export interface UpdateCourseData {
    course_code?: string
    course_name?: string
    description?: string
    duration_minutes?: number
    is_active?: boolean
}

export const coursesApi = {
    async list(params?: {
        page?: number
        per_page?: number
        search?: string
        is_active?: boolean
    }): Promise<{ data: CourseListResponse | null, error: any }> {
        try {
            const queryParams = new URLSearchParams()
            if (params?.page) queryParams.set('page', params.page.toString())
            if (params?.per_page) queryParams.set('per_page', params.per_page.toString())
            if (params?.search) queryParams.set('search', params.search)
            if (params?.is_active !== undefined) queryParams.set('is_active', params.is_active.toString())

            const url = `${API_BASE_URL}/api/v1/courses${queryParams.toString() ? '?' + queryParams.toString() : ''}`

            const response = await fetch(url, {
                method: 'GET',
                credentials: 'include',
            })

            if (!response.ok) {
                const error = await response.json()
                return { data: null, error: { message: error.detail || '取得課程列表失敗' } }
            }

            const result: CourseListResponse = await response.json()
            return { data: result, error: null }
        } catch (err) {
            return { data: null, error: { message: '網路錯誤，請稍後再試' } }
        }
    },

    async get(courseId: string): Promise<{ data: Course | null, error: any }> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/courses/${courseId}`, {
                method: 'GET',
                credentials: 'include',
            })

            if (!response.ok) {
                const error = await response.json()
                return { data: null, error: { message: error.detail || '取得課程失敗' } }
            }

            const result: CourseResponse = await response.json()
            return { data: result.data || null, error: null }
        } catch (err) {
            return { data: null, error: { message: '網路錯誤，請稍後再試' } }
        }
    },

    async create(data: CreateCourseData): Promise<{ data: Course | null, error: any }> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/courses`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(data),
            })

            if (!response.ok) {
                const error = await response.json()
                return { data: null, error: { message: error.detail || '建立課程失敗' } }
            }

            const result: CourseResponse = await response.json()
            return { data: result.data || null, error: null }
        } catch (err) {
            return { data: null, error: { message: '網路錯誤，請稍後再試' } }
        }
    },

    async update(courseId: string, data: UpdateCourseData): Promise<{ data: Course | null, error: any }> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/courses/${courseId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                credentials: 'include',
                body: JSON.stringify(data),
            })

            if (!response.ok) {
                const error = await response.json()
                return { data: null, error: { message: error.detail || '更新課程失敗' } }
            }

            const result: CourseResponse = await response.json()
            return { data: result.data || null, error: null }
        } catch (err) {
            return { data: null, error: { message: '網路錯誤，請稍後再試' } }
        }
    },

    async delete(courseId: string): Promise<{ success: boolean, error: any }> {
        try {
            const response = await fetch(`${API_BASE_URL}/api/v1/courses/${courseId}`, {
                method: 'DELETE',
                credentials: 'include',
            })

            if (!response.ok) {
                const error = await response.json()
                return { success: false, error: { message: error.detail || '刪除課程失敗' } }
            }

            return { success: true, error: null }
        } catch (err) {
            return { success: false, error: { message: '網路錯誤，請稍後再試' } }
        }
    },
}

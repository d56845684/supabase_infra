'use client'

import { useState, useEffect, useCallback } from 'react'
import { useAuth } from '@/lib/hooks/useAuth'
import { coursesApi, Course, CreateCourseData, UpdateCourseData } from '@/lib/api/courses'
import { Plus, Pencil, Trash2, Search, X, BookOpen, Clock, CheckCircle, XCircle } from 'lucide-react'
import DashboardLayout from '@/components/DashboardLayout'

export default function CoursesPage() {
    const { user, profile } = useAuth()

    // State
    const [courses, setCourses] = useState<Course[]>([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined)

    // Pagination
    const [page, setPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)
    const [total, setTotal] = useState(0)
    const perPage = 10

    // Modal state
    const [showModal, setShowModal] = useState(false)
    const [modalMode, setModalMode] = useState<'create' | 'edit'>('create')
    const [editingCourse, setEditingCourse] = useState<Course | null>(null)
    const [formData, setFormData] = useState<CreateCourseData>({
        course_code: '',
        course_name: '',
        description: '',
        duration_minutes: 60,
        is_active: true,
    })
    const [formError, setFormError] = useState<string | null>(null)
    const [submitting, setSubmitting] = useState(false)

    // Delete confirmation
    const [deleteConfirm, setDeleteConfirm] = useState<Course | null>(null)
    const [deleting, setDeleting] = useState(false)

    // Fetch courses
    const fetchCourses = useCallback(async () => {
        setLoading(true)
        setError(null)

        const { data, error } = await coursesApi.list({
            page,
            per_page: perPage,
            search: searchTerm || undefined,
            is_active: filterActive,
        })

        if (error) {
            setError(error.message)
        } else if (data) {
            setCourses(data.data)
            setTotalPages(data.total_pages)
            setTotal(data.total)
        }

        setLoading(false)
    }, [page, searchTerm, filterActive])

    useEffect(() => {
        if (user) {
            fetchCourses()
        }
    }, [user, fetchCourses])

    // Search with debounce
    useEffect(() => {
        const timer = setTimeout(() => {
            setPage(1)
        }, 300)
        return () => clearTimeout(timer)
    }, [searchTerm])

    // Modal handlers
    const openCreateModal = () => {
        setModalMode('create')
        setEditingCourse(null)
        setFormData({
            course_code: '',
            course_name: '',
            description: '',
            duration_minutes: 60,
            is_active: true,
        })
        setFormError(null)
        setShowModal(true)
    }

    const openEditModal = (course: Course) => {
        setModalMode('edit')
        setEditingCourse(course)
        setFormData({
            course_code: course.course_code,
            course_name: course.course_name,
            description: course.description || '',
            duration_minutes: course.duration_minutes,
            is_active: course.is_active,
        })
        setFormError(null)
        setShowModal(true)
    }

    const closeModal = () => {
        setShowModal(false)
        setEditingCourse(null)
        setFormError(null)
    }

    // Form submit
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault()
        setFormError(null)
        setSubmitting(true)

        try {
            if (modalMode === 'create') {
                const { data, error } = await coursesApi.create(formData)
                if (error) {
                    setFormError(error.message)
                } else {
                    closeModal()
                    fetchCourses()
                }
            } else if (editingCourse) {
                const updateData: UpdateCourseData = {}
                if (formData.course_code !== editingCourse.course_code) updateData.course_code = formData.course_code
                if (formData.course_name !== editingCourse.course_name) updateData.course_name = formData.course_name
                if (formData.description !== editingCourse.description) updateData.description = formData.description
                if (formData.duration_minutes !== editingCourse.duration_minutes) updateData.duration_minutes = formData.duration_minutes
                if (formData.is_active !== editingCourse.is_active) updateData.is_active = formData.is_active

                const { data, error } = await coursesApi.update(editingCourse.id, updateData)
                if (error) {
                    setFormError(error.message)
                } else {
                    closeModal()
                    fetchCourses()
                }
            }
        } finally {
            setSubmitting(false)
        }
    }

    // Delete handler
    const handleDelete = async () => {
        if (!deleteConfirm) return
        setDeleting(true)

        const { success, error } = await coursesApi.delete(deleteConfirm.id)

        if (error) {
            setError(error.message)
        } else {
            setDeleteConfirm(null)
            fetchCourses()
        }

        setDeleting(false)
    }

    const isStaff = profile?.role === 'admin' || profile?.role === 'employee'

    return (
        <DashboardLayout>
            <div className="py-8">
                <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
                    {/* Header */}
                    <div className="mb-8">
                        <div className="flex items-center justify-between">
                            <div>
                                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                                    <BookOpen className="w-8 h-8 text-blue-600" />
                                    課程管理
                                </h1>
                                <p className="mt-2 text-gray-600">
                                    共 {total} 個課程
                                </p>
                            </div>
                            {isStaff && (
                                <button
                                    onClick={openCreateModal}
                                    className="btn-primary flex items-center gap-2"
                                >
                                    <Plus className="w-5 h-5" />
                                    新增課程
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Filters */}
                    <div className="card mb-6">
                        <div className="flex flex-col sm:flex-row gap-4">
                            {/* Search */}
                            <div className="flex-1 relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                <input
                                    type="text"
                                    placeholder="搜尋課程代碼或名稱..."
                                    value={searchTerm}
                                    onChange={(e) => setSearchTerm(e.target.value)}
                                    className="input-field pl-10"
                                />
                                {searchTerm && (
                                    <button
                                        onClick={() => setSearchTerm('')}
                                        className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                )}
                            </div>

                            {/* Filter by status */}
                            <select
                                value={filterActive === undefined ? 'all' : filterActive ? 'active' : 'inactive'}
                                onChange={(e) => {
                                    const value = e.target.value
                                    setFilterActive(value === 'all' ? undefined : value === 'active')
                                    setPage(1)
                                }}
                                className="input-field w-full sm:w-48"
                            >
                                <option value="all">全部狀態</option>
                                <option value="active">啟用中</option>
                                <option value="inactive">已停用</option>
                            </select>
                        </div>
                    </div>

                    {/* Error */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
                            {error}
                        </div>
                    )}

                    {/* Course List */}
                    {loading ? (
                        <div className="flex justify-center py-12">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        </div>
                    ) : courses.length === 0 ? (
                        <div className="card text-center py-12">
                            <BookOpen className="w-16 h-16 mx-auto text-gray-300 mb-4" />
                            <h3 className="text-lg font-medium text-gray-900 mb-2">沒有找到課程</h3>
                            <p className="text-gray-500">
                                {searchTerm ? '請嘗試其他搜尋條件' : '點擊「新增課程」建立第一個課程'}
                            </p>
                        </div>
                    ) : (
                        <div className="card overflow-hidden">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            課程代碼
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            課程名稱
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            時長
                                        </th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                            狀態
                                        </th>
                                        {isStaff && (
                                            <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                操作
                                            </th>
                                        )}
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {courses.map((course) => (
                                        <tr key={course.id} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <span className="font-mono text-sm bg-gray-100 px-2 py-1 rounded">
                                                    {course.course_code}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4">
                                                <div>
                                                    <div className="font-medium text-gray-900">
                                                        {course.course_name}
                                                    </div>
                                                    {course.description && (
                                                        <div className="text-sm text-gray-500 truncate max-w-xs">
                                                            {course.description}
                                                        </div>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                <div className="flex items-center text-gray-600">
                                                    <Clock className="w-4 h-4 mr-1" />
                                                    {course.duration_minutes} 分鐘
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap">
                                                {course.is_active ? (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                                                        <CheckCircle className="w-3 h-3 mr-1" />
                                                        啟用中
                                                    </span>
                                                ) : (
                                                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                                                        <XCircle className="w-3 h-3 mr-1" />
                                                        已停用
                                                    </span>
                                                )}
                                            </td>
                                            {isStaff && (
                                                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                    <button
                                                        onClick={() => openEditModal(course)}
                                                        className="text-blue-600 hover:text-blue-900 mr-4"
                                                        title="編輯"
                                                    >
                                                        <Pencil className="w-5 h-5" />
                                                    </button>
                                                    <button
                                                        onClick={() => setDeleteConfirm(course)}
                                                        className="text-red-600 hover:text-red-900"
                                                        title="刪除"
                                                    >
                                                        <Trash2 className="w-5 h-5" />
                                                    </button>
                                                </td>
                                            )}
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* Pagination */}
                    {totalPages > 1 && (
                        <div className="mt-6 flex items-center justify-between">
                            <div className="text-sm text-gray-500">
                                顯示 {(page - 1) * perPage + 1} - {Math.min(page * perPage, total)} 共 {total} 項
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => setPage(p => Math.max(1, p - 1))}
                                    disabled={page === 1}
                                    className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    上一頁
                                </button>
                                <span className="px-4 py-2 text-gray-600">
                                    {page} / {totalPages}
                                </span>
                                <button
                                    onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                                    disabled={page === totalPages}
                                    className="btn-secondary disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    下一頁
                                </button>
                            </div>
                        </div>
                    )}
                </div>

                {/* Create/Edit Modal */}
                {showModal && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-xl shadow-xl max-w-lg w-full max-h-[90vh] overflow-y-auto">
                            <div className="p-6">
                                <div className="flex items-center justify-between mb-6">
                                    <h2 className="text-xl font-bold text-gray-900">
                                        {modalMode === 'create' ? '新增課程' : '編輯課程'}
                                    </h2>
                                    <button
                                        onClick={closeModal}
                                        className="text-gray-400 hover:text-gray-600"
                                    >
                                        <X className="w-6 h-6" />
                                    </button>
                                </div>

                                {formError && (
                                    <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                                        {formError}
                                    </div>
                                )}

                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            課程代碼 <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="text"
                                            value={formData.course_code}
                                            onChange={(e) => setFormData({ ...formData, course_code: e.target.value })}
                                            className="input-field"
                                            placeholder="例如：ENG101"
                                            required
                                            maxLength={50}
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            課程名稱 <span className="text-red-500">*</span>
                                        </label>
                                        <input
                                            type="text"
                                            value={formData.course_name}
                                            onChange={(e) => setFormData({ ...formData, course_name: e.target.value })}
                                            className="input-field"
                                            placeholder="例如：基礎英語會話"
                                            required
                                            maxLength={200}
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            課程描述
                                        </label>
                                        <textarea
                                            value={formData.description}
                                            onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                            className="input-field"
                                            placeholder="課程內容說明..."
                                            rows={3}
                                        />
                                    </div>

                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">
                                            課程時長（分鐘）
                                        </label>
                                        <input
                                            type="number"
                                            value={formData.duration_minutes}
                                            onChange={(e) => setFormData({ ...formData, duration_minutes: parseInt(e.target.value) || 60 })}
                                            className="input-field"
                                            min={15}
                                            max={480}
                                        />
                                    </div>

                                    <div className="flex items-center">
                                        <input
                                            type="checkbox"
                                            id="is_active"
                                            checked={formData.is_active}
                                            onChange={(e) => setFormData({ ...formData, is_active: e.target.checked })}
                                            className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                                        />
                                        <label htmlFor="is_active" className="ml-2 block text-sm text-gray-700">
                                            啟用課程
                                        </label>
                                    </div>

                                    <div className="flex gap-3 pt-4">
                                        <button
                                            type="button"
                                            onClick={closeModal}
                                            className="btn-secondary flex-1"
                                            disabled={submitting}
                                        >
                                            取消
                                        </button>
                                        <button
                                            type="submit"
                                            className="btn-primary flex-1"
                                            disabled={submitting}
                                        >
                                            {submitting ? (
                                                <span className="flex items-center justify-center">
                                                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                                    處理中...
                                                </span>
                                            ) : modalMode === 'create' ? '建立' : '儲存'}
                                        </button>
                                    </div>
                                </form>
                            </div>
                        </div>
                    </div>
                )}

                {/* Delete Confirmation Modal */}
                {deleteConfirm && (
                    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
                        <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
                            <h3 className="text-lg font-bold text-gray-900 mb-2">
                                確認刪除課程
                            </h3>
                            <p className="text-gray-600 mb-6">
                                確定要刪除課程「<span className="font-medium">{deleteConfirm.course_name}</span>」嗎？
                                此操作無法復原。
                            </p>
                            <div className="flex gap-3">
                                <button
                                    onClick={() => setDeleteConfirm(null)}
                                    className="btn-secondary flex-1"
                                    disabled={deleting}
                                >
                                    取消
                                </button>
                                <button
                                    onClick={handleDelete}
                                    className="btn-danger flex-1"
                                    disabled={deleting}
                                >
                                    {deleting ? (
                                        <span className="flex items-center justify-center">
                                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                                            刪除中...
                                        </span>
                                    ) : '確認刪除'}
                                </button>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </DashboardLayout>
    )
}

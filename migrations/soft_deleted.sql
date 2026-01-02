-- ==========================================
-- 軟刪除欄位設計 Migration
-- ==========================================

-- ==========================================
-- 1. 新增軟刪除欄位到所有表格
-- ==========================================

-- user_profiles
ALTER TABLE public.user_profiles 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- students
ALTER TABLE public.students 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- student_contracts
ALTER TABLE public.student_contracts 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- course_purchases
ALTER TABLE public.course_purchases 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- teachers
ALTER TABLE public.teachers 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- teacher_contracts
ALTER TABLE public.teacher_contracts 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- teacher_payroll
ALTER TABLE public.teacher_payroll 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- zoom_accounts
ALTER TABLE public.zoom_accounts 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- bookings
ALTER TABLE public.bookings 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- attendance_records
ALTER TABLE public.attendance_records 
ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS deleted_by UUID REFERENCES public.user_profiles(id) DEFAULT NULL;

-- role_change_audit（審計日誌通常不做軟刪除）

-- ==========================================
-- 2. 建立索引（加速查詢未刪除的資料）
-- ==========================================

CREATE INDEX IF NOT EXISTS idx_user_profiles_deleted_at ON public.user_profiles(deleted_at);
CREATE INDEX IF NOT EXISTS idx_students_deleted_at ON public.students(deleted_at);
CREATE INDEX IF NOT EXISTS idx_student_contracts_deleted_at ON public.student_contracts(deleted_at);
CREATE INDEX IF NOT EXISTS idx_course_purchases_deleted_at ON public.course_purchases(deleted_at);
CREATE INDEX IF NOT EXISTS idx_teachers_deleted_at ON public.teachers(deleted_at);
CREATE INDEX IF NOT EXISTS idx_teacher_contracts_deleted_at ON public.teacher_contracts(deleted_at);
CREATE INDEX IF NOT EXISTS idx_teacher_payroll_deleted_at ON public.teacher_payroll(deleted_at);
CREATE INDEX IF NOT EXISTS idx_zoom_accounts_deleted_at ON public.zoom_accounts(deleted_at);
CREATE INDEX IF NOT EXISTS idx_bookings_deleted_at ON public.bookings(deleted_at);
CREATE INDEX IF NOT EXISTS idx_attendance_records_deleted_at ON public.attendance_records(deleted_at);

-- 複合索引（常用查詢：未刪除 + 其他條件）
CREATE INDEX IF NOT EXISTS idx_students_active ON public.students(student_status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_teachers_active ON public.teachers(teacher_status) WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_bookings_active ON public.bookings(status, scheduled_start) WHERE deleted_at IS NULL;

-- ==========================================
-- 3. 建立 View（方便查詢未刪除的資料）
-- ==========================================

-- 活躍的使用者
CREATE OR REPLACE VIEW public.v_active_user_profiles AS
SELECT * FROM public.user_profiles WHERE deleted_at IS NULL;

-- 活躍的學生
CREATE OR REPLACE VIEW public.v_active_students AS
SELECT s.*, up.full_name, up.email, up.phone
FROM public.students s
JOIN public.user_profiles up ON up.id = s.id
WHERE s.deleted_at IS NULL AND up.deleted_at IS NULL;

-- 活躍的老師
CREATE OR REPLACE VIEW public.v_active_teachers AS
SELECT t.*, up.full_name, up.email, up.phone
FROM public.teachers t
JOIN public.user_profiles up ON up.id = t.id
WHERE t.deleted_at IS NULL AND up.deleted_at IS NULL;

-- 活躍的預約
CREATE OR REPLACE VIEW public.v_active_bookings AS
SELECT 
    b.*,
    sup.full_name AS student_name,
    tup.full_name AS teacher_name
FROM public.bookings b
JOIN public.user_profiles sup ON sup.id = b.student_id
JOIN public.user_profiles tup ON tup.id = b.teacher_id
WHERE b.deleted_at IS NULL;

-- ==========================================
-- 4. 軟刪除函式(optional)
-- ==========================================

-- 通用軟刪除函式
-- CREATE OR REPLACE FUNCTION public.soft_delete(
--     table_name TEXT,
--     record_id UUID
-- )
-- RETURNS BOOLEAN AS $$
-- BEGIN
--     EXECUTE format(
--         'UPDATE public.%I SET deleted_at = NOW(), deleted_by = $1 WHERE id = $2 AND deleted_at IS NULL',
--         table_name
--     ) USING auth.uid(), record_id;
    
--     RETURN FOUND;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- -- 軟刪除學生（連同相關資料）
-- CREATE OR REPLACE FUNCTION public.soft_delete_student(student_id UUID)
-- RETURNS BOOLEAN AS $$
-- BEGIN
--     -- 檢查權限
--     IF NOT EXISTS (
--         SELECT 1 FROM public.user_profiles 
--         WHERE id = auth.uid() AND role = 'admin'
--     ) THEN
--         RAISE EXCEPTION 'Only admins can delete students';
--     END IF;

--     -- 軟刪除 user_profile
--     UPDATE public.user_profiles 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE id = student_id AND deleted_at IS NULL;

--     -- 軟刪除 student
--     UPDATE public.students 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE id = student_id AND deleted_at IS NULL;

--     -- 軟刪除相關合約
--     UPDATE public.student_contracts 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE student_id = soft_delete_student.student_id AND deleted_at IS NULL;

--     -- 軟刪除相關購買記錄
--     UPDATE public.course_purchases 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE student_id = soft_delete_student.student_id AND deleted_at IS NULL;

--     -- 軟刪除相關預約
--     UPDATE public.bookings 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE student_id = soft_delete_student.student_id AND deleted_at IS NULL;

--     RETURN TRUE;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- -- 軟刪除老師（連同相關資料）
-- CREATE OR REPLACE FUNCTION public.soft_delete_teacher(teacher_id UUID)
-- RETURNS BOOLEAN AS $$
-- BEGIN
--     -- 檢查權限
--     IF NOT EXISTS (
--         SELECT 1 FROM public.user_profiles 
--         WHERE id = auth.uid() AND role = 'admin'
--     ) THEN
--         RAISE EXCEPTION 'Only admins can delete teachers';
--     END IF;

--     -- 軟刪除 user_profile
--     UPDATE public.user_profiles 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE id = teacher_id AND deleted_at IS NULL;

--     -- 軟刪除 teacher
--     UPDATE public.teachers 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE id = teacher_id AND deleted_at IS NULL;

--     -- 軟刪除相關合約
--     UPDATE public.teacher_contracts 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE teacher_id = soft_delete_teacher.teacher_id AND deleted_at IS NULL;

--     -- 軟刪除相關薪資記錄
--     UPDATE public.teacher_payroll 
--     SET deleted_at = NOW(), deleted_by = auth.uid()
--     WHERE teacher_id = soft_delete_teacher.teacher_id AND deleted_at IS NULL;

--     RETURN TRUE;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- -- ==========================================
-- -- 5. 恢復函式
-- -- ==========================================

-- -- 恢復學生
-- CREATE OR REPLACE FUNCTION public.restore_student(student_id UUID)
-- RETURNS BOOLEAN AS $$
-- BEGIN
--     -- 檢查權限
--     IF NOT EXISTS (
--         SELECT 1 FROM public.user_profiles 
--         WHERE id = auth.uid() AND role = 'admin'
--     ) THEN
--         RAISE EXCEPTION 'Only admins can restore students';
--     END IF;

--     -- 恢復 user_profile
--     UPDATE public.user_profiles 
--     SET deleted_at = NULL, deleted_by = NULL, updated_at = NOW()
--     WHERE id = student_id AND deleted_at IS NOT NULL;

--     -- 恢復 student
--     UPDATE public.students 
--     SET deleted_at = NULL, deleted_by = NULL, updated_at = NOW()
--     WHERE id = student_id AND deleted_at IS NOT NULL;

--     RETURN TRUE;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- -- 恢復老師
-- CREATE OR REPLACE FUNCTION public.restore_teacher(teacher_id UUID)
-- RETURNS BOOLEAN AS $$
-- BEGIN
--     -- 檢查權限
--     IF NOT EXISTS (
--         SELECT 1 FROM public.user_profiles 
--         WHERE id = auth.uid() AND role = 'admin'
--     ) THEN
--         RAISE EXCEPTION 'Only admins can restore teachers';
--     END IF;

--     -- 恢復 user_profile
--     UPDATE public.user_profiles 
--     SET deleted_at = NULL, deleted_by = NULL, updated_at = NOW()
--     WHERE id = teacher_id AND deleted_at IS NOT NULL;

--     -- 恢復 teacher
--     UPDATE public.teachers 
--     SET deleted_at = NULL, deleted_by = NULL, updated_at = NOW()
--     WHERE id = teacher_id AND deleted_at IS NOT NULL;

--     RETURN TRUE;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- ==========================================
-- 6. 更新 RLS 政策（排除已刪除的資料）
-- ==========================================

-- 更新 user_profiles RLS
DROP POLICY IF EXISTS "Admin can view all profiles" ON public.user_profiles;
CREATE POLICY "Admin can view all profiles" ON public.user_profiles
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin' AND deleted_at IS NULL
        )
    );

DROP POLICY IF EXISTS "Users can view own profile" ON public.user_profiles;
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT TO authenticated
    USING (id = auth.uid() AND deleted_at IS NULL);

-- 更新 students RLS
DROP POLICY IF EXISTS "Admin can view all students" ON public.students;
CREATE POLICY "Admin can view all students" ON public.students
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin' AND deleted_at IS NULL
        )
    );

DROP POLICY IF EXISTS "Students can view own data" ON public.students;
CREATE POLICY "Students can view own data" ON public.students
    FOR SELECT TO authenticated
    USING (id = auth.uid() AND deleted_at IS NULL);

-- 更新 teachers RLS
DROP POLICY IF EXISTS "Admin can view all teachers" ON public.teachers;
CREATE POLICY "Admin can view all teachers" ON public.teachers
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin' AND deleted_at IS NULL
        )
    );

DROP POLICY IF EXISTS "Teachers can view own data" ON public.teachers;
CREATE POLICY "Teachers can view own data" ON public.teachers
    FOR SELECT TO authenticated
    USING (id = auth.uid() AND deleted_at IS NULL);

DROP POLICY IF EXISTS "Students can view active teachers" ON public.teachers;
CREATE POLICY "Students can view active teachers" ON public.teachers
    FOR SELECT TO authenticated
    USING (
        teacher_status = 'active' 
        AND deleted_at IS NULL
        AND EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'student' AND deleted_at IS NULL
        )
    );

-- 更新 bookings RLS
DROP POLICY IF EXISTS "Admin can manage all bookings" ON public.bookings;
CREATE POLICY "Admin can manage all bookings" ON public.bookings
    FOR ALL TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin' AND deleted_at IS NULL
        )
    );

DROP POLICY IF EXISTS "Students can view own bookings" ON public.bookings;
CREATE POLICY "Students can view own bookings" ON public.bookings
    FOR SELECT TO authenticated
    USING (student_id = auth.uid() AND deleted_at IS NULL);

DROP POLICY IF EXISTS "Teachers can view own bookings" ON public.bookings;
CREATE POLICY "Teachers can view own bookings" ON public.bookings
    FOR SELECT TO authenticated
    USING (teacher_id = auth.uid() AND deleted_at IS NULL);

-- ==========================================
-- 7. 定期清理硬刪除（選用）
-- ==========================================

-- 硬刪除超過 90 天的軟刪除資料
-- CREATE OR REPLACE FUNCTION public.purge_deleted_records(days_old INTEGER DEFAULT 90)
-- RETURNS TABLE(table_name TEXT, deleted_count INTEGER) AS $$
-- DECLARE
--     cutoff_date TIMESTAMP WITH TIME ZONE;
--     r RECORD;
--     cnt INTEGER;
-- BEGIN
--     cutoff_date := NOW() - (days_old || ' days')::INTERVAL;
    
--     FOR r IN 
--         SELECT t.table_name 
--         FROM information_schema.columns c
--         JOIN information_schema.tables t ON t.table_name = c.table_name
--         WHERE c.column_name = 'deleted_at' 
--         AND t.table_schema = 'public'
--         AND t.table_type = 'BASE TABLE'
--     LOOP
--         EXECUTE format(
--             'DELETE FROM public.%I WHERE deleted_at < $1',
--             r.table_name
--         ) USING cutoff_date;
        
--         GET DIAGNOSTICS cnt = ROW_COUNT;
        
--         IF cnt > 0 THEN
--             table_name := r.table_name;
--             deleted_count := cnt;
--             RETURN NEXT;
--         END IF;
--     END LOOP;
-- END;
-- $$ LANGUAGE plpgsql SECURITY DEFINER;

-- 使用方式（只有 admin 可執行）
-- SELECT * FROM public.purge_deleted_records(90);

-- ==========================================
-- 8. 刪除審計日誌
-- ==========================================

CREATE TABLE IF NOT EXISTS public.deletion_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    record_id UUID NOT NULL,
    deleted_data JSONB,
    deleted_by UUID REFERENCES public.user_profiles(id),
    deleted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    restored_at TIMESTAMP WITH TIME ZONE,
    restored_by UUID REFERENCES public.user_profiles(id)
);

-- 審計日誌 RLS
ALTER TABLE public.deletion_audit ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admin can view deletion audit" ON public.deletion_audit
    FOR SELECT TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin' AND deleted_at IS NULL
        )
    );
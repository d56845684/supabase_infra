-- ============================================
-- 教育管理系統 Row Level Security (RLS) 政策
-- 適用於 Supabase
-- ============================================

-- ============================================
-- 1. 用戶角色對照表 (連結 Supabase Auth)
-- ============================================

-- 用戶角色類型
CREATE TYPE user_role AS ENUM ('admin', 'employee', 'teacher', 'student');

-- 用戶資料對照表
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL,
    employee_id UUID REFERENCES employees(id),
    teacher_id UUID REFERENCES teachers(id),
    student_id UUID REFERENCES students(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- 確保角色對應正確的關聯 ID
    CONSTRAINT chk_role_reference CHECK (
        (role = 'admin' AND employee_id IS NOT NULL) OR
        (role = 'employee' AND employee_id IS NOT NULL) OR
        (role = 'teacher' AND teacher_id IS NOT NULL) OR
        (role = 'student' AND student_id IS NOT NULL)
    )
);

CREATE INDEX idx_user_profiles_employee ON user_profiles(employee_id);
CREATE INDEX idx_user_profiles_teacher ON user_profiles(teacher_id);
CREATE INDEX idx_user_profiles_student ON user_profiles(student_id);

-- ============================================
-- 2. 輔助函數：取得當前用戶資訊
-- ============================================

-- 取得當前用戶角色
CREATE OR REPLACE FUNCTION auth.get_user_role()
RETURNS user_role AS $$
    SELECT role FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 取得當前用戶的員工 ID
CREATE OR REPLACE FUNCTION auth.get_employee_id()
RETURNS UUID AS $$
    SELECT employee_id FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 取得當前用戶的教師 ID
CREATE OR REPLACE FUNCTION auth.get_teacher_id()
RETURNS UUID AS $$
    SELECT teacher_id FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 取得當前用戶的學生 ID
CREATE OR REPLACE FUNCTION auth.get_student_id()
RETURNS UUID AS $$
    SELECT student_id FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查是否為管理員
CREATE OR REPLACE FUNCTION auth.is_admin()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM user_profiles 
        WHERE id = auth.uid() 
        AND role = 'admin'
        AND is_active = TRUE
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查是否為員工（含管理員）
CREATE OR REPLACE FUNCTION auth.is_staff()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM user_profiles 
        WHERE id = auth.uid() 
        AND role IN ('admin', 'employee')
        AND is_active = TRUE
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================
-- 3. 啟用所有表格的 RLS
-- ============================================

ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE employees ENABLE ROW LEVEL SECURITY;
ALTER TABLE courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE course_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_courses ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_contract_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_contract_extra_lessons ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_contract_detail_extensions ENABLE ROW LEVEL SECURITY;
ALTER TABLE student_contract_teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_contract_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_contract_detail_extensions ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_available_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE substitute_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE leave_records ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 4. user_profiles 政策
-- ============================================

-- 用戶只能查看自己的資料
CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (id = auth.uid());

-- 管理員可查看所有
CREATE POLICY "Admins can view all profiles"
    ON user_profiles FOR SELECT
    USING (auth.is_admin());

-- 只有管理員可以建立/修改
CREATE POLICY "Admins can manage profiles"
    ON user_profiles FOR ALL
    USING (auth.is_admin());

-- ============================================
-- 5. employees 員工表政策
-- ============================================

-- 員工可查看所有員工（基本資訊）
CREATE POLICY "Staff can view employees"
    ON employees FOR SELECT
    USING (auth.is_staff() AND is_deleted = FALSE);

-- 只有管理員可以管理員工
CREATE POLICY "Admins can manage employees"
    ON employees FOR ALL
    USING (auth.is_admin());

-- ============================================
-- 6. courses 課程表政策
-- ============================================

-- 所有已登入用戶可查看課程
CREATE POLICY "Authenticated users can view courses"
    ON courses FOR SELECT
    USING (auth.uid() IS NOT NULL AND is_deleted = FALSE);

-- 員工可以管理課程
CREATE POLICY "Staff can manage courses"
    ON courses FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 7. course_details 課程明細政策
-- ============================================

CREATE POLICY "Authenticated users can view course details"
    ON course_details FOR SELECT
    USING (auth.uid() IS NOT NULL AND is_deleted = FALSE);

CREATE POLICY "Staff can manage course details"
    ON course_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 8. teachers 教師表政策
-- ============================================

-- 所有已登入用戶可查看教師基本資訊
CREATE POLICY "Authenticated users can view teachers"
    ON teachers FOR SELECT
    USING (auth.uid() IS NOT NULL AND is_deleted = FALSE);

-- 教師可以更新自己的資料
CREATE POLICY "Teachers can update own profile"
    ON teachers FOR UPDATE
    USING (id = auth.get_teacher_id())
    WITH CHECK (id = auth.get_teacher_id());

-- 員工可以管理教師
CREATE POLICY "Staff can manage teachers"
    ON teachers FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 9. teacher_details 教師明細政策
-- ============================================

-- 教師可查看自己的明細
CREATE POLICY "Teachers can view own details"
    ON teacher_details FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

-- 員工可查看所有
CREATE POLICY "Staff can view all teacher details"
    ON teacher_details FOR SELECT
    USING (auth.is_staff() AND is_deleted = FALSE);

-- 員工可管理
CREATE POLICY "Staff can manage teacher details"
    ON teacher_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 10. students 學生表政策
-- ============================================

-- 學生可查看自己的資料
CREATE POLICY "Students can view own profile"
    ON students FOR SELECT
    USING (id = auth.get_student_id() AND is_deleted = FALSE);

-- 學生可更新自己的基本資料
CREATE POLICY "Students can update own profile"
    ON students FOR UPDATE
    USING (id = auth.get_student_id())
    WITH CHECK (id = auth.get_student_id());

-- 教師可查看有預約關係的學生
CREATE POLICY "Teachers can view related students"
    ON students FOR SELECT
    USING (
        auth.get_teacher_id() IS NOT NULL 
        AND is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.student_id = students.id
            AND b.teacher_id = auth.get_teacher_id()
            AND b.is_deleted = FALSE
        )
    );

-- 員工可以管理學生
CREATE POLICY "Staff can manage students"
    ON students FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 11. student_details 學生明細政策
-- ============================================

CREATE POLICY "Students can view own details"
    ON student_details FOR SELECT
    USING (student_id = auth.get_student_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage student details"
    ON student_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 12. student_courses 學生選課政策
-- ============================================

-- 學生可查看自己的選課
CREATE POLICY "Students can view own courses"
    ON student_courses FOR SELECT
    USING (student_id = auth.get_student_id() AND is_deleted = FALSE);

-- 員工可管理
CREATE POLICY "Staff can manage student courses"
    ON student_courses FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 13. student_contracts 學生合約政策
-- ============================================

-- 學生可查看自己的合約
CREATE POLICY "Students can view own contracts"
    ON student_contracts FOR SELECT
    USING (student_id = auth.get_student_id() AND is_deleted = FALSE);

-- 教師可查看相關合約（被指派的）
CREATE POLICY "Teachers can view assigned contracts"
    ON student_contracts FOR SELECT
    USING (
        is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM student_contract_teachers sct
            WHERE sct.student_contract_id = student_contracts.id
            AND sct.teacher_id = auth.get_teacher_id()
            AND sct.is_deleted = FALSE
        )
    );

-- 員工可管理
CREATE POLICY "Staff can manage student contracts"
    ON student_contracts FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 14. student_contract_details 學生合約明細政策
-- ============================================

CREATE POLICY "Students can view own contract details"
    ON student_contract_details FOR SELECT
    USING (
        is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM student_contracts sc
            WHERE sc.id = student_contract_details.student_contract_id
            AND sc.student_id = auth.get_student_id()
        )
    );

CREATE POLICY "Staff can manage contract details"
    ON student_contract_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 15. student_contract_extra_lessons 學生合約額外堂數政策
-- ============================================

CREATE POLICY "Students can view own extra lessons"
    ON student_contract_extra_lessons FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM student_contracts sc
            WHERE sc.id = student_contract_extra_lessons.student_contract_id
            AND sc.student_id = auth.get_student_id()
        )
    );

CREATE POLICY "Staff can manage extra lessons"
    ON student_contract_extra_lessons FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 16. student_contract_detail_extensions 學生合約明細延展政策
-- ============================================

CREATE POLICY "Students can view own contract detail extensions"
    ON student_contract_detail_extensions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM student_contract_details scd
            JOIN student_contracts sc ON sc.id = scd.student_contract_id
            WHERE scd.id = student_contract_detail_extensions.student_contract_detail_id
            AND sc.student_id = auth.get_student_id()
        )
    );

CREATE POLICY "Staff can manage contract detail extensions"
    ON student_contract_detail_extensions FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 17. student_contract_teachers 專屬教師政策
-- ============================================

-- 學生可查看自己合約的專屬教師
CREATE POLICY "Students can view own assigned teachers"
    ON student_contract_teachers FOR SELECT
    USING (
        is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM student_contracts sc
            WHERE sc.id = student_contract_teachers.student_contract_id
            AND sc.student_id = auth.get_student_id()
        )
    );

-- 教師可查看自己被指派的記錄
CREATE POLICY "Teachers can view own assignments"
    ON student_contract_teachers FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage contract teachers"
    ON student_contract_teachers FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 18. teacher_contracts 教師合約政策
-- ============================================

-- 教師只能查看自己的合約
CREATE POLICY "Teachers can view own contracts"
    ON teacher_contracts FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage teacher contracts"
    ON teacher_contracts FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 19. teacher_contract_details 教師合約明細政策
-- ============================================

-- 教師可查看自己的合約明細（薪資）
CREATE POLICY "Teachers can view own contract details"
    ON teacher_contract_details FOR SELECT
    USING (
        is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM teacher_contracts tc
            WHERE tc.id = teacher_contract_details.teacher_contract_id
            AND tc.teacher_id = auth.get_teacher_id()
        )
    );

CREATE POLICY "Staff can manage teacher contract details"
    ON teacher_contract_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 20. teacher_contract_detail_extensions 教師合約明細延展政策
-- ============================================

CREATE POLICY "Teachers can view own contract detail extensions"
    ON teacher_contract_detail_extensions FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM teacher_contract_details tcd
            JOIN teacher_contracts tc ON tc.id = tcd.teacher_contract_id
            WHERE tcd.id = teacher_contract_detail_extensions.teacher_contract_detail_id
            AND tc.teacher_id = auth.get_teacher_id()
        )
    );

CREATE POLICY "Staff can manage teacher contract detail extensions"
    ON teacher_contract_detail_extensions FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 21. teacher_available_slots 教師時段政策
-- ============================================

-- 所有已登入用戶可查看可用時段（用於預約）
CREATE POLICY "Authenticated users can view available slots"
    ON teacher_available_slots FOR SELECT
    USING (auth.uid() IS NOT NULL AND is_deleted = FALSE);

-- 教師可以管理自己的時段
CREATE POLICY "Teachers can manage own slots"
    ON teacher_available_slots FOR INSERT
    WITH CHECK (teacher_id = auth.get_teacher_id());

CREATE POLICY "Teachers can update own slots"
    ON teacher_available_slots FOR UPDATE
    USING (teacher_id = auth.get_teacher_id())
    WITH CHECK (teacher_id = auth.get_teacher_id());

CREATE POLICY "Teachers can delete own slots"
    ON teacher_available_slots FOR DELETE
    USING (teacher_id = auth.get_teacher_id() AND is_booked = FALSE);

-- 員工可管理所有時段
CREATE POLICY "Staff can manage all slots"
    ON teacher_available_slots FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 19. bookings 預約主檔政策
-- ============================================

-- 學生可查看自己的預約
CREATE POLICY "Students can view own bookings"
    ON bookings FOR SELECT
    USING (student_id = auth.get_student_id() AND is_deleted = FALSE);

-- 學生可以建立預約
CREATE POLICY "Students can create bookings"
    ON bookings FOR INSERT
    WITH CHECK (student_id = auth.get_student_id());

-- 學生可以取消自己的預約（更新狀態）
CREATE POLICY "Students can cancel own bookings"
    ON bookings FOR UPDATE
    USING (student_id = auth.get_student_id() AND booking_status = 'pending')
    WITH CHECK (student_id = auth.get_student_id());

-- 教師可查看自己的預約
CREATE POLICY "Teachers can view own bookings"
    ON bookings FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

-- 教師可更新預約狀態
CREATE POLICY "Teachers can update own bookings"
    ON bookings FOR UPDATE
    USING (teacher_id = auth.get_teacher_id())
    WITH CHECK (teacher_id = auth.get_teacher_id());

-- 員工可管理所有預約
CREATE POLICY "Staff can manage all bookings"
    ON bookings FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 20. booking_details 預約明細政策
-- ============================================

-- 學生可查看自己預約的明細
CREATE POLICY "Students can view own booking details"
    ON booking_details FOR SELECT
    USING (
        is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.id = booking_details.booking_id
            AND b.student_id = auth.get_student_id()
        )
    );

-- 教師可查看和更新自己預約的明細
CREATE POLICY "Teachers can view own booking details"
    ON booking_details FOR SELECT
    USING (
        is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.id = booking_details.booking_id
            AND b.teacher_id = auth.get_teacher_id()
        )
    );

CREATE POLICY "Teachers can update own booking details"
    ON booking_details FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.id = booking_details.booking_id
            AND b.teacher_id = auth.get_teacher_id()
        )
    );

CREATE POLICY "Staff can manage booking details"
    ON booking_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 21. substitute_details 代課明細政策
-- ============================================

-- 原教師可查看自己課程的代課記錄
CREATE POLICY "Original teachers can view substitute details"
    ON substitute_details FOR SELECT
    USING (
        is_deleted = FALSE
        AND EXISTS (
            SELECT 1 FROM bookings b
            WHERE b.id = substitute_details.booking_id
            AND b.teacher_id = auth.get_teacher_id()
        )
    );

-- 代課教師可查看自己的代課記錄
CREATE POLICY "Substitute teachers can view own records"
    ON substitute_details FOR SELECT
    USING (substitute_teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage substitute details"
    ON substitute_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 22. leave_records 請假明細政策
-- ============================================

-- 學生可查看和建立自己的請假
CREATE POLICY "Students can view own leave records"
    ON leave_records FOR SELECT
    USING (initiator_student_id = auth.get_student_id() AND is_deleted = FALSE);

CREATE POLICY "Students can create leave requests"
    ON leave_records FOR INSERT
    WITH CHECK (
        initiator_type = 'student' 
        AND initiator_student_id = auth.get_student_id()
    );

-- 教師可查看和建立自己的請假
CREATE POLICY "Teachers can view own leave records"
    ON leave_records FOR SELECT
    USING (initiator_teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Teachers can create leave requests"
    ON leave_records FOR INSERT
    WITH CHECK (
        initiator_type = 'teacher'
        AND initiator_teacher_id = auth.get_teacher_id()
    );

-- 員工可查看所有請假記錄
CREATE POLICY "Staff can view all leave records"
    ON leave_records FOR SELECT
    USING (auth.is_staff() AND is_deleted = FALSE);

-- 員工可審核請假（更新）
CREATE POLICY "Staff can approve leave requests"
    ON leave_records FOR UPDATE
    USING (auth.is_staff());

-- 管理員可完全管理
CREATE POLICY "Admins can manage leave records"
    ON leave_records FOR ALL
    USING (auth.is_admin());

-- ============================================
-- 23. Service Role 繞過 RLS（用於後端 API）
-- ============================================

-- 注意：Supabase 的 service_role 預設會繞過 RLS
-- 確保只在安全的後端環境使用 service_role key

-- ============================================
-- 24. 授權 anon 和 authenticated 角色
-- ============================================

-- 授權 authenticated 用戶存取所有表格（受 RLS 限制）
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- anon 只能存取公開資料（如課程列表）
GRANT SELECT ON courses TO anon;
GRANT SELECT ON teachers TO anon;

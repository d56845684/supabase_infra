-- ============================================
-- 教育管理系統 Row Level Security (RLS) 政策
-- 整合自多個遷移檔案
-- ============================================

-- ============================================
-- 1. 輔助函數：取得當前用戶資訊
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

-- 取得當前用戶的員工子類型
CREATE OR REPLACE FUNCTION auth.get_employee_type()
RETURNS employee_type AS $$
    SELECT employee_subtype FROM user_profiles WHERE id = auth.uid();
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 取得當前用戶的權限等級
CREATE OR REPLACE FUNCTION auth.get_employee_permission_level()
RETURNS INT AS $$
DECLARE
    v_employee_type employee_type;
    v_level INT;
BEGIN
    SELECT employee_subtype INTO v_employee_type
    FROM user_profiles
    WHERE id = auth.uid();

    IF v_employee_type IS NULL THEN
        RETURN 0;
    END IF;

    SELECT permission_level INTO v_level
    FROM employee_permission_levels
    WHERE employee_type = v_employee_type;

    RETURN COALESCE(v_level, 0);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

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
        SELECT 1 FROM user_profiles up
        LEFT JOIN employees e ON up.employee_id = e.id
        WHERE up.id = auth.uid()
        AND up.role IN ('admin', 'employee')
        AND up.is_active = TRUE
        AND (e.id IS NULL OR e.is_active = TRUE)
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查是否有指定的最低權限等級
CREATE OR REPLACE FUNCTION auth.has_permission_level(required_level INT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN auth.get_employee_permission_level() >= required_level;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER STABLE;

-- 檢查是否為工讀生以上（等級 >= 10）
CREATE OR REPLACE FUNCTION auth.is_intern_or_above()
RETURNS BOOLEAN AS $$
    SELECT auth.has_permission_level(10);
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查是否為兼職以上（等級 >= 20）
CREATE OR REPLACE FUNCTION auth.is_part_time_or_above()
RETURNS BOOLEAN AS $$
    SELECT auth.has_permission_level(20);
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查是否為正職以上（等級 >= 30）
CREATE OR REPLACE FUNCTION auth.is_full_time_or_above()
RETURNS BOOLEAN AS $$
    SELECT auth.has_permission_level(30);
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- ============================================
-- 2. Line 整合輔助函數
-- ============================================

-- 透過 Line User ID 和頻道類型取得用戶 ID
CREATE OR REPLACE FUNCTION get_user_by_line_id(
    p_line_user_id VARCHAR,
    p_channel_type line_channel_type DEFAULT 'student'
)
RETURNS UUID AS $$
    SELECT user_id FROM line_user_bindings
    WHERE line_user_id = p_line_user_id
    AND channel_type = p_channel_type
    AND binding_status = 'active';
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 檢查用戶在特定頻道是否已綁定 Line
CREATE OR REPLACE FUNCTION is_line_bound(
    p_user_id UUID,
    p_channel_type line_channel_type DEFAULT NULL
)
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM line_user_bindings
        WHERE user_id = p_user_id
        AND binding_status = 'active'
        AND (p_channel_type IS NULL OR channel_type = p_channel_type)
    );
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 透過 email 查找已綁定 Line 的用戶
CREATE OR REPLACE FUNCTION find_user_by_line_email(p_email VARCHAR)
RETURNS UUID AS $$
    SELECT id FROM auth.users
    WHERE email = p_email;
$$ LANGUAGE sql SECURITY DEFINER STABLE;

-- 取得用戶在特定頻道的 Line User ID
CREATE OR REPLACE FUNCTION get_line_user_id_by_channel(
    p_user_id UUID,
    p_channel_type line_channel_type
)
RETURNS VARCHAR AS $$
    SELECT line_user_id FROM line_user_bindings
    WHERE user_id = p_user_id
    AND channel_type = p_channel_type
    AND binding_status = 'active';
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
ALTER TABLE student_contract_teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_contract_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE teacher_available_slots ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE booking_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE substitute_details ENABLE ROW LEVEL SECURITY;
ALTER TABLE leave_records ENABLE ROW LEVEL SECURITY;
ALTER TABLE employee_permission_levels ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_user_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE line_notification_logs ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 4. user_profiles 政策
-- ============================================

CREATE POLICY "Users can view own profile"
    ON user_profiles FOR SELECT
    USING (id = auth.uid());

CREATE POLICY "Admins can view all profiles"
    ON user_profiles FOR SELECT
    USING (auth.is_admin());

CREATE POLICY "Admins can manage profiles"
    ON user_profiles FOR ALL
    USING (auth.is_admin());

-- ============================================
-- 5. employees 員工表政策
-- ============================================

CREATE POLICY "Staff can view employees"
    ON employees FOR SELECT
    USING (auth.is_staff() AND is_deleted = FALSE);

CREATE POLICY "Admins can manage employees"
    ON employees FOR ALL
    USING (auth.is_admin());

-- ============================================
-- 6. courses 課程表政策
-- ============================================

CREATE POLICY "Authenticated users can view courses"
    ON courses FOR SELECT
    USING (auth.uid() IS NOT NULL AND is_deleted = FALSE);

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

CREATE POLICY "Authenticated users can view teachers"
    ON teachers FOR SELECT
    USING (auth.uid() IS NOT NULL AND is_deleted = FALSE);

CREATE POLICY "Teachers can update own profile"
    ON teachers FOR UPDATE
    USING (id = auth.get_teacher_id())
    WITH CHECK (id = auth.get_teacher_id());

CREATE POLICY "Staff can manage teachers"
    ON teachers FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 9. teacher_details 教師明細政策
-- ============================================

CREATE POLICY "Teachers can view own details"
    ON teacher_details FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can view all teacher details"
    ON teacher_details FOR SELECT
    USING (auth.is_staff() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage teacher details"
    ON teacher_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 10. students 學生表政策
-- ============================================

CREATE POLICY "Students can view own profile"
    ON students FOR SELECT
    USING (id = auth.get_student_id() AND is_deleted = FALSE);

CREATE POLICY "Students can update own profile"
    ON students FOR UPDATE
    USING (id = auth.get_student_id())
    WITH CHECK (id = auth.get_student_id());

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

CREATE POLICY "Students can view own courses"
    ON student_courses FOR SELECT
    USING (student_id = auth.get_student_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage student courses"
    ON student_courses FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 13. student_contracts 學生合約政策
-- ============================================

CREATE POLICY "Students can view own contracts"
    ON student_contracts FOR SELECT
    USING (student_id = auth.get_student_id() AND is_deleted = FALSE);

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
-- 15. student_contract_teachers 專屬教師政策
-- ============================================

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

CREATE POLICY "Teachers can view own assignments"
    ON student_contract_teachers FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage contract teachers"
    ON student_contract_teachers FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 16. teacher_contracts 教師合約政策
-- ============================================

CREATE POLICY "Teachers can view own contracts"
    ON teacher_contracts FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage teacher contracts"
    ON teacher_contracts FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 17. teacher_contract_details 教師合約明細政策
-- ============================================

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
-- 18. teacher_available_slots 教師時段政策
-- ============================================

CREATE POLICY "Authenticated users can view available slots"
    ON teacher_available_slots FOR SELECT
    USING (auth.uid() IS NOT NULL AND is_deleted = FALSE);

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

CREATE POLICY "Staff can manage all slots"
    ON teacher_available_slots FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 19. bookings 預約主檔政策
-- ============================================

CREATE POLICY "Students can view own bookings"
    ON bookings FOR SELECT
    USING (student_id = auth.get_student_id() AND is_deleted = FALSE);

CREATE POLICY "Students can create bookings"
    ON bookings FOR INSERT
    WITH CHECK (student_id = auth.get_student_id());

CREATE POLICY "Students can cancel own bookings"
    ON bookings FOR UPDATE
    USING (student_id = auth.get_student_id() AND booking_status = 'pending')
    WITH CHECK (student_id = auth.get_student_id());

CREATE POLICY "Teachers can view own bookings"
    ON bookings FOR SELECT
    USING (teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Teachers can update own bookings"
    ON bookings FOR UPDATE
    USING (teacher_id = auth.get_teacher_id())
    WITH CHECK (teacher_id = auth.get_teacher_id());

CREATE POLICY "Staff can manage all bookings"
    ON bookings FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 20. booking_details 預約明細政策
-- ============================================

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

CREATE POLICY "Substitute teachers can view own records"
    ON substitute_details FOR SELECT
    USING (substitute_teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Staff can manage substitute details"
    ON substitute_details FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 22. leave_records 請假明細政策
-- ============================================

CREATE POLICY "Students can view own leave records"
    ON leave_records FOR SELECT
    USING (initiator_student_id = auth.get_student_id() AND is_deleted = FALSE);

CREATE POLICY "Students can create leave requests"
    ON leave_records FOR INSERT
    WITH CHECK (
        initiator_type = 'student'
        AND initiator_student_id = auth.get_student_id()
    );

CREATE POLICY "Teachers can view own leave records"
    ON leave_records FOR SELECT
    USING (initiator_teacher_id = auth.get_teacher_id() AND is_deleted = FALSE);

CREATE POLICY "Teachers can create leave requests"
    ON leave_records FOR INSERT
    WITH CHECK (
        initiator_type = 'teacher'
        AND initiator_teacher_id = auth.get_teacher_id()
    );

CREATE POLICY "Staff can view all leave records"
    ON leave_records FOR SELECT
    USING (auth.is_staff() AND is_deleted = FALSE);

CREATE POLICY "Staff can approve leave requests"
    ON leave_records FOR UPDATE
    USING (auth.is_staff());

CREATE POLICY "Admins can manage leave records"
    ON leave_records FOR ALL
    USING (auth.is_admin());

-- ============================================
-- 23. employee_permission_levels 權限等級政策
-- ============================================

CREATE POLICY "Authenticated users can view permission levels"
    ON employee_permission_levels FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "Only admins can manage permission levels"
    ON employee_permission_levels FOR ALL
    USING (auth.is_admin());

-- ============================================
-- 24. line_user_bindings Line 綁定政策
-- ============================================

CREATE POLICY "Users can view own line binding"
    ON line_user_bindings FOR SELECT
    USING (user_id IS NOT NULL AND user_id = auth.uid());

CREATE POLICY "Users can insert own line binding"
    ON line_user_bindings FOR INSERT
    WITH CHECK (user_id = auth.uid());

CREATE POLICY "Users can update own line binding"
    ON line_user_bindings FOR UPDATE
    USING (user_id IS NOT NULL AND user_id = auth.uid());

CREATE POLICY "Users can delete own line binding"
    ON line_user_bindings FOR DELETE
    USING (user_id IS NOT NULL AND user_id = auth.uid());

CREATE POLICY "Staff can view all line bindings"
    ON line_user_bindings FOR SELECT
    USING (auth.is_staff());

-- ============================================
-- 25. line_notification_logs 通知日誌政策
-- ============================================

CREATE POLICY "Users can view own notifications"
    ON line_notification_logs FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "Staff can view all notifications"
    ON line_notification_logs FOR SELECT
    USING (auth.is_staff());

CREATE POLICY "Staff can manage notifications"
    ON line_notification_logs FOR ALL
    USING (auth.is_staff());

-- ============================================
-- 26. 授權設定
-- ============================================

-- 授權 authenticated 用戶存取所有表格（受 RLS 限制）
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- anon 只能存取公開資料
GRANT SELECT ON courses TO anon;
GRANT SELECT ON teachers TO anon;

-- 權限等級表
GRANT SELECT ON employee_permission_levels TO authenticated;

-- Line 綁定
GRANT SELECT, INSERT, UPDATE, DELETE ON line_user_bindings TO authenticated;

-- Line 通知日誌
GRANT SELECT ON line_notification_logs TO authenticated;
GRANT INSERT, UPDATE ON line_notification_logs TO service_role;

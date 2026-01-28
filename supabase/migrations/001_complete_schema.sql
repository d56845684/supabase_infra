-- ============================================
-- 教育管理系統 完整資料庫架構
-- Database: PostgreSQL (Supabase)
-- 整合自多個遷移檔案
-- ============================================

-- ============================================
-- 1. 啟用必要擴展
-- ============================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- ============================================
-- 2. 枚舉類型定義
-- ============================================

-- 員工類型
CREATE TYPE employee_type AS ENUM ('admin', 'full_time', 'part_time', 'intern');

-- 合約狀態
CREATE TYPE contract_status AS ENUM ('active', 'expired', 'terminated', 'pending');

-- 預約狀態
CREATE TYPE booking_status AS ENUM ('pending', 'confirmed', 'completed', 'cancelled');

-- 請假狀態
CREATE TYPE leave_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');

-- 請假發動者類型
CREATE TYPE leave_initiator_type AS ENUM ('student', 'teacher');

-- 用戶角色類型
CREATE TYPE user_role AS ENUM ('admin', 'employee', 'teacher', 'student');

-- Line 綁定狀態
CREATE TYPE line_binding_status AS ENUM ('pending', 'active', 'unlinked');

-- Line 頻道類型
CREATE TYPE line_channel_type AS ENUM ('student', 'teacher', 'employee');

-- 通知類型
CREATE TYPE notification_type AS ENUM (
    'booking_confirmation',
    'booking_reminder',
    'booking_cancelled',
    'status_update',
    'general'
);

-- 通知狀態
CREATE TYPE notification_status AS ENUM (
    'pending',
    'sent',
    'failed',
    'skipped'
);

-- ============================================
-- 3. 員工主檔 (employees)
-- ============================================
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_no VARCHAR(50) UNIQUE NOT NULL,
    employee_type employee_type NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    hire_date DATE NOT NULL,
    termination_date DATE,
    is_active BOOLEAN DEFAULT TRUE,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID,
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID
);

CREATE INDEX idx_employees_type ON employees(employee_type) WHERE is_deleted = FALSE;
CREATE INDEX idx_employees_email ON employees(email) WHERE is_deleted = FALSE;

-- ============================================
-- 4. 課程主檔 (courses)
-- ============================================
CREATE TABLE courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_code VARCHAR(50) UNIQUE NOT NULL,
    course_name VARCHAR(200) NOT NULL,
    description TEXT,
    duration_minutes INT DEFAULT 60,
    is_active BOOLEAN DEFAULT TRUE,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_courses_code ON courses(course_code) WHERE is_deleted = FALSE;

-- ============================================
-- 5. 課程明細 (course_details)
-- ============================================
CREATE TABLE course_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    course_id UUID NOT NULL REFERENCES courses(id),
    detail_type VARCHAR(50) NOT NULL,
    content TEXT,
    sort_order INT DEFAULT 0,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_course_details_course ON course_details(course_id) WHERE is_deleted = FALSE;

-- ============================================
-- 6. 教師主檔 (teachers)
-- ============================================
CREATE TABLE teachers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_no VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    bio TEXT,
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_teachers_no ON teachers(teacher_no) WHERE is_deleted = FALSE;
CREATE INDEX idx_teachers_email ON teachers(email) WHERE is_deleted = FALSE;

-- ============================================
-- 7. 教師明細 (teacher_details)
-- ============================================
CREATE TABLE teacher_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id),
    detail_type VARCHAR(50) NOT NULL,
    content TEXT,
    issue_date DATE,
    expiry_date DATE,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_teacher_details_teacher ON teacher_details(teacher_id) WHERE is_deleted = FALSE;

-- ============================================
-- 8. 學生主檔 (students)
-- ============================================
CREATE TABLE students (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_no VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    birth_date DATE,
    avatar_url TEXT,
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    is_active BOOLEAN DEFAULT TRUE,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_students_no ON students(student_no) WHERE is_deleted = FALSE;
CREATE INDEX idx_students_email ON students(email) WHERE is_deleted = FALSE;

-- ============================================
-- 9. 學生明細 (student_details)
-- ============================================
CREATE TABLE student_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id),
    detail_type VARCHAR(50) NOT NULL,
    content TEXT,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_student_details_student ON student_details(student_id) WHERE is_deleted = FALSE;

-- ============================================
-- 10. 學生課程關聯表 (student_courses)
-- ============================================
CREATE TABLE student_courses (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES students(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    enrolled_at TIMESTAMPTZ DEFAULT NOW(),

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id),

    UNIQUE(student_id, course_id)
);

CREATE INDEX idx_student_courses_student ON student_courses(student_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_student_courses_course ON student_courses(course_id) WHERE is_deleted = FALSE;

-- ============================================
-- 11. 學生合約主檔 (student_contracts)
-- ============================================
CREATE TABLE student_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_no VARCHAR(50) UNIQUE NOT NULL,
    student_id UUID NOT NULL REFERENCES students(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    contract_status contract_status DEFAULT 'pending',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_lessons INT NOT NULL,
    remaining_lessons INT NOT NULL,
    price_per_lesson DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    notes TEXT,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_student_contracts_student ON student_contracts(student_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_student_contracts_course ON student_contracts(course_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_student_contracts_status ON student_contracts(contract_status) WHERE is_deleted = FALSE;

-- ============================================
-- 12. 學生合約明細 (student_contract_details)
-- ============================================
CREATE TABLE student_contract_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_contract_id UUID NOT NULL REFERENCES student_contracts(id),
    detail_type VARCHAR(50) NOT NULL,
    content TEXT,
    amount DECIMAL(10,2),
    effective_date DATE,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_student_contract_details_contract ON student_contract_details(student_contract_id) WHERE is_deleted = FALSE;

-- ============================================
-- 13. 學生合約專屬教師關聯表 (student_contract_teachers)
-- ============================================
CREATE TABLE student_contract_teachers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_contract_id UUID NOT NULL REFERENCES student_contracts(id),
    teacher_id UUID NOT NULL REFERENCES teachers(id),
    is_primary BOOLEAN DEFAULT FALSE,
    assigned_at TIMESTAMPTZ DEFAULT NOW(),

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id),

    UNIQUE(student_contract_id, teacher_id)
);

CREATE INDEX idx_contract_teachers_contract ON student_contract_teachers(student_contract_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_contract_teachers_teacher ON student_contract_teachers(teacher_id) WHERE is_deleted = FALSE;

-- ============================================
-- 14. 教師合約主檔 (teacher_contracts)
-- ============================================
CREATE TABLE teacher_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    contract_no VARCHAR(50) UNIQUE NOT NULL,
    teacher_id UUID NOT NULL REFERENCES teachers(id),
    contract_status contract_status DEFAULT 'pending',
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    base_salary DECIMAL(10,2),
    notes TEXT,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_teacher_contracts_teacher ON teacher_contracts(teacher_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_teacher_contracts_status ON teacher_contracts(contract_status) WHERE is_deleted = FALSE;

-- ============================================
-- 15. 教師合約明細 - 課程薪資 (teacher_contract_details)
-- ============================================
CREATE TABLE teacher_contract_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_contract_id UUID NOT NULL REFERENCES teacher_contracts(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    hourly_rate DECIMAL(10,2) NOT NULL,
    rate_type VARCHAR(50) DEFAULT 'fixed',
    rate_percentage DECIMAL(5,2),
    effective_date DATE NOT NULL,
    expiry_date DATE,
    notes TEXT,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id),

    UNIQUE(teacher_contract_id, course_id, effective_date)
);

CREATE INDEX idx_teacher_contract_details_contract ON teacher_contract_details(teacher_contract_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_teacher_contract_details_course ON teacher_contract_details(course_id) WHERE is_deleted = FALSE;

-- ============================================
-- 16. 教師授課時段表明細 (teacher_available_slots)
-- ============================================
CREATE TABLE teacher_available_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES teachers(id),
    teacher_contract_id UUID REFERENCES teacher_contracts(id),
    slot_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    is_available BOOLEAN DEFAULT TRUE,
    is_booked BOOLEAN DEFAULT FALSE,
    recurrence_rule VARCHAR(100),
    notes TEXT,
    time_range TSRANGE,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_teacher_slots_teacher ON teacher_available_slots(teacher_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_teacher_slots_date ON teacher_available_slots(slot_date) WHERE is_deleted = FALSE AND is_available = TRUE;
CREATE INDEX idx_teacher_slots_available ON teacher_available_slots(is_available, is_booked) WHERE is_deleted = FALSE;

-- 教師時段排除約束：防止同一教師的時段重疊
ALTER TABLE teacher_available_slots
ADD CONSTRAINT excl_teacher_slot_overlap
EXCLUDE USING gist (
    teacher_id WITH =,
    time_range WITH &&
) WHERE (is_deleted = FALSE);

-- ============================================
-- 17. 預約主檔 (bookings)
-- ============================================
CREATE TABLE bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_no VARCHAR(50) UNIQUE NOT NULL,
    student_id UUID NOT NULL REFERENCES students(id),
    teacher_id UUID NOT NULL REFERENCES teachers(id),
    course_id UUID NOT NULL REFERENCES courses(id),
    student_contract_id UUID NOT NULL REFERENCES student_contracts(id),
    teacher_contract_id UUID NOT NULL REFERENCES teacher_contracts(id),
    teacher_slot_id UUID NOT NULL REFERENCES teacher_available_slots(id),
    teacher_hourly_rate DECIMAL(10,2) NOT NULL,
    teacher_rate_percentage DECIMAL(5,2),
    substitute_detail_id UUID,
    booking_status booking_status DEFAULT 'pending',
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    notes TEXT,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_bookings_student ON bookings(student_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_bookings_teacher ON bookings(teacher_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_bookings_date ON bookings(booking_date) WHERE is_deleted = FALSE;
CREATE INDEX idx_bookings_status ON bookings(booking_status) WHERE is_deleted = FALSE;

-- ============================================
-- 18. 預約明細表 (booking_details)
-- ============================================
CREATE TABLE booking_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES bookings(id),
    lessons_used INT DEFAULT 1,
    zoom_link TEXT,
    zoom_meeting_id VARCHAR(100),
    zoom_password VARCHAR(50),
    recording_url TEXT,
    recording_storage_path TEXT,
    recording_duration_seconds INT,
    attendance_status VARCHAR(20) DEFAULT 'pending',
    teacher_notes TEXT,
    student_feedback TEXT,
    rating INT CHECK (rating >= 1 AND rating <= 5),

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_booking_details_booking ON booking_details(booking_id) WHERE is_deleted = FALSE;

-- ============================================
-- 19. 代課明細表 (substitute_details)
-- ============================================
CREATE TABLE substitute_details (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES bookings(id),
    substitute_teacher_id UUID NOT NULL REFERENCES teachers(id),
    substitute_contract_id UUID NOT NULL REFERENCES teacher_contracts(id),
    substitute_hourly_rate DECIMAL(10,2),
    reason TEXT,
    approved_by UUID REFERENCES employees(id),
    approved_at TIMESTAMPTZ,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id)
);

CREATE INDEX idx_substitute_booking ON substitute_details(booking_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_substitute_teacher ON substitute_details(substitute_teacher_id) WHERE is_deleted = FALSE;

-- 添加 bookings 表的代課外鍵
ALTER TABLE bookings
ADD CONSTRAINT fk_bookings_substitute
FOREIGN KEY (substitute_detail_id) REFERENCES substitute_details(id);

-- ============================================
-- 20. 請假明細表 (leave_records)
-- ============================================
CREATE TABLE leave_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    leave_no VARCHAR(50) UNIQUE NOT NULL,
    initiator_type leave_initiator_type NOT NULL,
    initiator_student_id UUID REFERENCES students(id),
    initiator_teacher_id UUID REFERENCES teachers(id),
    booking_id UUID REFERENCES bookings(id),
    leave_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    reason TEXT NOT NULL,
    leave_status leave_status DEFAULT 'pending',
    approver_id UUID REFERENCES employees(id),
    approved_at TIMESTAMPTZ,
    rejection_reason TEXT,

    -- 審計欄位
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID REFERENCES employees(id),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by UUID REFERENCES employees(id),
    is_deleted BOOLEAN DEFAULT FALSE,
    deleted_at TIMESTAMPTZ,
    deleted_by UUID REFERENCES employees(id),

    -- 確保只有一個發動者
    CONSTRAINT chk_initiator CHECK (
        (initiator_type = 'student' AND initiator_student_id IS NOT NULL AND initiator_teacher_id IS NULL) OR
        (initiator_type = 'teacher' AND initiator_teacher_id IS NOT NULL AND initiator_student_id IS NULL)
    )
);

CREATE INDEX idx_leave_student ON leave_records(initiator_student_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_leave_teacher ON leave_records(initiator_teacher_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_leave_date ON leave_records(leave_date) WHERE is_deleted = FALSE;
CREATE INDEX idx_leave_status ON leave_records(leave_status) WHERE is_deleted = FALSE;
CREATE INDEX idx_leave_approver ON leave_records(approver_id) WHERE is_deleted = FALSE;

-- ============================================
-- 21. 用戶資料對照表 (user_profiles)
-- ============================================
CREATE TABLE user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL,
    employee_id UUID REFERENCES employees(id),
    teacher_id UUID REFERENCES teachers(id),
    student_id UUID REFERENCES students(id),
    employee_subtype employee_type,
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
-- 22. 員工權限等級對照表 (employee_permission_levels)
-- ============================================
CREATE TABLE employee_permission_levels (
    employee_type employee_type PRIMARY KEY,
    permission_level INT NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 插入權限等級資料
INSERT INTO employee_permission_levels (employee_type, permission_level, description) VALUES
    ('intern', 10, '工讀生 - 基本讀取權限'),
    ('part_time', 20, '兼職員工 - 有限的寫入權限'),
    ('full_time', 30, '正式員工 - 完整操作權限'),
    ('admin', 100, '管理員 - 系統完整權限');

-- ============================================
-- 23. Line 用戶綁定表 (line_user_bindings)
-- ============================================
CREATE TABLE line_user_bindings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE,
    line_user_id VARCHAR(50) NOT NULL,
    line_display_name VARCHAR(100),
    line_picture_url TEXT,
    line_email VARCHAR(255),
    binding_status line_binding_status DEFAULT 'active',
    channel_type line_channel_type NOT NULL DEFAULT 'student',
    notify_booking_confirmation BOOLEAN DEFAULT TRUE,
    notify_booking_reminder BOOLEAN DEFAULT TRUE,
    notify_status_update BOOLEAN DEFAULT TRUE,
    bound_at TIMESTAMPTZ DEFAULT NOW(),
    unbound_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- 同一 Line 帳號在同一頻道只能綁定一個用戶
    CONSTRAINT unique_line_channel UNIQUE(line_user_id, channel_type)
);

-- user_id 可為 NULL，使用 partial unique index
CREATE UNIQUE INDEX idx_unique_user_channel_active
    ON line_user_bindings(user_id, channel_type)
    WHERE user_id IS NOT NULL;

CREATE INDEX idx_line_bindings_user ON line_user_bindings(user_id);
CREATE INDEX idx_line_bindings_user_channel ON line_user_bindings(user_id, channel_type);
CREATE INDEX idx_line_bindings_line_user ON line_user_bindings(line_user_id);
CREATE INDEX idx_line_bindings_line_channel ON line_user_bindings(line_user_id, channel_type);
CREATE INDEX idx_line_bindings_email ON line_user_bindings(line_email) WHERE line_email IS NOT NULL;
CREATE INDEX idx_line_bindings_status ON line_user_bindings(binding_status);
CREATE INDEX idx_line_bindings_channel_type ON line_user_bindings(channel_type);

-- ============================================
-- 24. Line 通知日誌表 (line_notification_logs)
-- ============================================
CREATE TABLE line_notification_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
    line_user_id VARCHAR(50) NOT NULL,
    channel_type line_channel_type NOT NULL DEFAULT 'student',
    notification_type notification_type NOT NULL,
    reference_id UUID,
    reference_type VARCHAR(50),
    message_template VARCHAR(100),
    message_content TEXT,
    notification_status notification_status DEFAULT 'pending',
    line_message_id VARCHAR(100),
    error_message TEXT,
    retry_count INT DEFAULT 0,
    sent_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_notification_logs_user ON line_notification_logs(user_id);
CREATE INDEX idx_notification_logs_line_user ON line_notification_logs(line_user_id);
CREATE INDEX idx_notification_logs_channel ON line_notification_logs(channel_type);
CREATE INDEX idx_notification_logs_status ON line_notification_logs(notification_status);
CREATE INDEX idx_notification_logs_type ON line_notification_logs(notification_type);
CREATE INDEX idx_notification_logs_reference ON line_notification_logs(reference_type, reference_id);
CREATE INDEX idx_notification_logs_created ON line_notification_logs(created_at DESC);
CREATE INDEX idx_notification_logs_pending
    ON line_notification_logs(notification_status, created_at)
    WHERE notification_status = 'pending';

-- ============================================
-- 25. 觸發器函數
-- ============================================

-- 自動更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Line 綁定 updated_at
CREATE OR REPLACE FUNCTION update_line_binding_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 計算時段時間範圍
CREATE OR REPLACE FUNCTION calculate_slot_time_range()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.time_range := tsrange(
        (NEW.slot_date + NEW.start_time)::timestamp,
        (NEW.slot_date + NEW.end_time)::timestamp,
        '[)'
    );
    RETURN NEW;
END;
$$;

-- 檢查教師時段重疊
CREATE OR REPLACE FUNCTION check_teacher_slot_overlap()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_conflict_id UUID;
    v_conflict_date DATE;
    v_conflict_start TIME;
    v_conflict_end TIME;
BEGIN
    SELECT id, slot_date, start_time, end_time
    INTO v_conflict_id, v_conflict_date, v_conflict_start, v_conflict_end
    FROM teacher_available_slots
    WHERE teacher_id = NEW.teacher_id
      AND id != COALESCE(NEW.id, '00000000-0000-0000-0000-000000000000'::uuid)
      AND is_deleted = FALSE
      AND slot_date = NEW.slot_date
      AND (
          (NEW.start_time >= start_time AND NEW.start_time < end_time)
          OR
          (NEW.end_time > start_time AND NEW.end_time <= end_time)
          OR
          (NEW.start_time <= start_time AND NEW.end_time >= end_time)
      )
    LIMIT 1;

    IF v_conflict_id IS NOT NULL THEN
        RAISE EXCEPTION '時段衝突：該教師在 % 已有 % - % 的授課時段，無法建立重疊時段',
            v_conflict_date,
            v_conflict_start::TEXT,
            v_conflict_end::TEXT;
    END IF;

    RETURN NEW;
END;
$$;

-- 同步員工子類型
CREATE OR REPLACE FUNCTION sync_employee_subtype()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.employee_id IS NOT NULL THEN
        SELECT employee_type INTO NEW.employee_subtype
        FROM employees
        WHERE id = NEW.employee_id;
    ELSE
        NEW.employee_subtype = NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 建立用戶實體
CREATE OR REPLACE FUNCTION create_user_entity()
RETURNS TRIGGER AS $$
DECLARE
    v_entity_id UUID;
BEGIN
    CASE NEW.role
        WHEN 'student' THEN
            INSERT INTO students (student_no, name, email, is_active)
            VALUES (
                'S' || UPPER(SUBSTRING(NEW.id::text, 1, 8)),
                COALESCE((SELECT raw_user_meta_data->>'name' FROM auth.users WHERE id = NEW.id), 'New Student'),
                (SELECT email FROM auth.users WHERE id = NEW.id),
                TRUE
            )
            RETURNING id INTO v_entity_id;
            NEW.student_id := v_entity_id;

        WHEN 'teacher' THEN
            INSERT INTO teachers (teacher_no, name, email, is_active)
            VALUES (
                'T' || UPPER(SUBSTRING(NEW.id::text, 1, 8)),
                COALESCE((SELECT raw_user_meta_data->>'name' FROM auth.users WHERE id = NEW.id), 'New Teacher'),
                (SELECT email FROM auth.users WHERE id = NEW.id),
                TRUE
            )
            RETURNING id INTO v_entity_id;
            NEW.teacher_id := v_entity_id;

        WHEN 'employee', 'admin' THEN
            INSERT INTO employees (employee_no, name, email, employee_type, hire_date, is_active)
            VALUES (
                'E' || UPPER(SUBSTRING(NEW.id::text, 1, 8)),
                COALESCE((SELECT raw_user_meta_data->>'name' FROM auth.users WHERE id = NEW.id), 'New Employee'),
                (SELECT email FROM auth.users WHERE id = NEW.id),
                CASE
                    WHEN NEW.role = 'admin' THEN 'admin'::employee_type
                    ELSE COALESCE(NEW.employee_subtype, 'intern'::employee_type)
                END,
                CURRENT_DATE,
                TRUE
            )
            RETURNING id INTO v_entity_id;
            NEW.employee_id := v_entity_id;
    END CASE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ============================================
-- 26. 建立觸發器
-- ============================================

-- 為所有表格建立 updated_at 觸發器
DO $$
DECLARE
    t TEXT;
BEGIN
    FOR t IN
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_type = 'BASE TABLE'
        AND table_name IN (
            'employees', 'courses', 'course_details', 'teachers', 'teacher_details',
            'students', 'student_details', 'student_courses', 'student_contracts',
            'student_contract_details', 'student_contract_teachers', 'teacher_contracts',
            'teacher_contract_details', 'teacher_available_slots', 'bookings',
            'booking_details', 'substitute_details', 'leave_records'
        )
    LOOP
        EXECUTE format('
            CREATE TRIGGER update_%I_updated_at
            BEFORE UPDATE ON %I
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column()
        ', t, t);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- 教師時段觸發器
CREATE TRIGGER trg_calculate_slot_time_range
    BEFORE INSERT OR UPDATE ON teacher_available_slots
    FOR EACH ROW
    EXECUTE FUNCTION calculate_slot_time_range();

CREATE TRIGGER trg_check_teacher_slot_overlap
    BEFORE INSERT OR UPDATE ON teacher_available_slots
    FOR EACH ROW
    EXECUTE FUNCTION check_teacher_slot_overlap();

-- Line 綁定 updated_at 觸發器
CREATE TRIGGER trg_line_bindings_updated_at
    BEFORE UPDATE ON line_user_bindings
    FOR EACH ROW
    EXECUTE FUNCTION update_line_binding_updated_at();

-- Line 通知日誌 updated_at 觸發器
CREATE TRIGGER trg_notification_logs_updated_at
    BEFORE UPDATE ON line_notification_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_line_binding_updated_at();

-- 用戶實體建立觸發器
CREATE TRIGGER trg_create_user_entity
    BEFORE INSERT ON user_profiles
    FOR EACH ROW
    WHEN (
        (NEW.role = 'student' AND NEW.student_id IS NULL) OR
        (NEW.role = 'teacher' AND NEW.teacher_id IS NULL) OR
        (NEW.role IN ('employee', 'admin') AND NEW.employee_id IS NULL)
    )
    EXECUTE FUNCTION create_user_entity();

-- 員工子類型同步觸發器
CREATE TRIGGER trg_sync_employee_subtype
    BEFORE INSERT OR UPDATE ON user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION sync_employee_subtype();

-- ============================================
-- 27. 輔助查詢函數
-- ============================================

-- 查詢教師某日所有時段
CREATE OR REPLACE FUNCTION get_teacher_daily_slots(
    p_teacher_id UUID,
    p_date DATE
)
RETURNS TABLE (
    slot_id UUID,
    slot_start_time TIME,
    slot_end_time TIME,
    slot_is_available BOOLEAN,
    slot_is_booked BOOLEAN
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        tas.id,
        tas.start_time,
        tas.end_time,
        tas.is_available,
        tas.is_booked
    FROM teacher_available_slots tas
    WHERE tas.teacher_id = p_teacher_id
      AND tas.slot_date = p_date
      AND tas.is_deleted = FALSE
    ORDER BY tas.start_time;
END;
$$;

-- 檢查特定時段是否可用
CREATE OR REPLACE FUNCTION check_slot_availability(
    p_teacher_id UUID,
    p_date DATE,
    p_start_time TIME,
    p_end_time TIME
)
RETURNS TABLE (
    slot_available BOOLEAN,
    conflict_message TEXT
)
LANGUAGE plpgsql
AS $$
DECLARE
    v_conflict_date DATE;
    v_conflict_start TIME;
    v_conflict_end TIME;
    v_found BOOLEAN := FALSE;
BEGIN
    SELECT tas.slot_date, tas.start_time, tas.end_time
    INTO v_conflict_date, v_conflict_start, v_conflict_end
    FROM teacher_available_slots tas
    WHERE tas.teacher_id = p_teacher_id
      AND tas.slot_date = p_date
      AND tas.is_deleted = FALSE
      AND (
          (p_start_time >= tas.start_time AND p_start_time < tas.end_time)
          OR (p_end_time > tas.start_time AND p_end_time <= tas.end_time)
          OR (p_start_time <= tas.start_time AND p_end_time >= tas.end_time)
      )
    LIMIT 1;

    v_found := FOUND;

    IF v_found THEN
        RETURN QUERY SELECT
            FALSE::BOOLEAN,
            FORMAT('與現有時段衝突: %s %s-%s',
                   v_conflict_date,
                   v_conflict_start::TEXT,
                   v_conflict_end::TEXT)::TEXT;
    ELSE
        RETURN QUERY SELECT TRUE::BOOLEAN, NULL::TEXT;
    END IF;
END;
$$;

-- ============================================
-- 28. 視圖
-- ============================================

-- 可用預約時段視圖
CREATE VIEW v_available_slots AS
SELECT
    tas.id,
    tas.slot_date,
    tas.start_time,
    tas.end_time,
    t.id AS teacher_id,
    t.name AS teacher_name,
    tc.id AS contract_id
FROM teacher_available_slots tas
JOIN teachers t ON tas.teacher_id = t.id
LEFT JOIN teacher_contracts tc ON tas.teacher_contract_id = tc.id
WHERE tas.is_deleted = FALSE
  AND tas.is_available = TRUE
  AND tas.is_booked = FALSE
  AND t.is_deleted = FALSE
  AND t.is_active = TRUE;

-- 學生合約摘要視圖
CREATE VIEW v_student_contract_summary AS
SELECT
    sc.id,
    sc.contract_no,
    s.name AS student_name,
    c.course_name,
    sc.total_lessons,
    sc.remaining_lessons,
    sc.contract_status,
    sc.start_date,
    sc.end_date,
    (
        SELECT STRING_AGG(t.name, ', ')
        FROM student_contract_teachers sct
        JOIN teachers t ON sct.teacher_id = t.id
        WHERE sct.student_contract_id = sc.id
        AND sct.is_deleted = FALSE
    ) AS assigned_teachers
FROM student_contracts sc
JOIN students s ON sc.student_id = s.id
JOIN courses c ON sc.course_id = c.id
WHERE sc.is_deleted = FALSE;

-- 通知統計視圖
CREATE OR REPLACE VIEW v_notification_stats AS
SELECT
    channel_type,
    notification_type,
    notification_status,
    COUNT(*) as count,
    DATE_TRUNC('day', created_at) as date
FROM line_notification_logs
GROUP BY channel_type, notification_type, notification_status, DATE_TRUNC('day', created_at);

-- 用戶通知偏好視圖
CREATE OR REPLACE VIEW v_user_notification_preferences AS
SELECT
    u.id as user_id,
    u.email,
    lb.channel_type,
    lb.line_user_id,
    lb.notify_booking_confirmation,
    lb.notify_booking_reminder,
    lb.notify_status_update,
    lb.binding_status
FROM auth.users u
LEFT JOIN line_user_bindings lb ON u.id = lb.user_id;

-- 員工權限視圖
CREATE OR REPLACE VIEW v_employee_permissions AS
SELECT
    e.id as employee_id,
    e.employee_no,
    e.name,
    e.employee_type,
    epl.permission_level,
    epl.description as permission_description,
    e.is_active,
    up.id as user_profile_id,
    up.role as user_role
FROM employees e
JOIN employee_permission_levels epl ON e.employee_type = epl.employee_type
LEFT JOIN user_profiles up ON up.employee_id = e.id
WHERE e.is_deleted = FALSE;

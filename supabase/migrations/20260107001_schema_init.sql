-- ============================================
-- 教育管理系統 資料庫架構設計
-- Database: PostgreSQL (Supabase)
-- ============================================

-- 啟用 UUID 擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- 1. 枚舉類型定義
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

-- ============================================
-- 2. 基礎共用欄位說明
-- ============================================
-- 所有表格都包含以下審計欄位：
-- id: UUID 主鍵
-- created_at: 建立時間
-- created_by: 建立者 UUID
-- updated_at: 更新時間
-- updated_by: 更新者 UUID
-- is_deleted: 軟刪除標記
-- deleted_at: 刪除時間
-- deleted_by: 刪除者 UUID

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
    detail_type VARCHAR(50) NOT NULL, -- 如: syllabus, material, requirement
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
    detail_type VARCHAR(50) NOT NULL, -- 如: certification, experience, specialty
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
    detail_type VARCHAR(50) NOT NULL, -- 如: note, preference, history
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
-- 10. 學生課程關聯表 (student_courses) - 一對多
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
    total_lessons INT NOT NULL, -- 總堂數
    remaining_lessons INT NOT NULL, -- 剩餘堂數
    price_per_lesson DECIMAL(10,2) NOT NULL, -- 每堂價格
    total_amount DECIMAL(12,2) NOT NULL, -- 合約總金額
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
    detail_type VARCHAR(50) NOT NULL, -- 如: payment, amendment, note
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
-- 13. 學生合約專屬教師關聯表 (student_contract_teachers) - 一對多
-- ============================================
CREATE TABLE student_contract_teachers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_contract_id UUID NOT NULL REFERENCES student_contracts(id),
    teacher_id UUID NOT NULL REFERENCES teachers(id),
    is_primary BOOLEAN DEFAULT FALSE, -- 是否為主要教師
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
    base_salary DECIMAL(10,2), -- 基本薪資(若有)
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
    hourly_rate DECIMAL(10,2) NOT NULL, -- 課程鐘點費
    rate_type VARCHAR(50) DEFAULT 'fixed', -- fixed, percentage
    rate_percentage DECIMAL(5,2), -- 若為百分比計算
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
    is_available BOOLEAN DEFAULT TRUE, -- 是否可預約
    is_booked BOOLEAN DEFAULT FALSE, -- 是否已被預約
    recurrence_rule VARCHAR(100), -- 重複規則 (如: WEEKLY)
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

CREATE INDEX idx_teacher_slots_teacher ON teacher_available_slots(teacher_id) WHERE is_deleted = FALSE;
CREATE INDEX idx_teacher_slots_date ON teacher_available_slots(slot_date) WHERE is_deleted = FALSE AND is_available = TRUE;
CREATE INDEX idx_teacher_slots_available ON teacher_available_slots(is_available, is_booked) WHERE is_deleted = FALSE;

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
    teacher_hourly_rate DECIMAL(10,2) NOT NULL, -- 教師課程鐘點費
    teacher_rate_percentage DECIMAL(5,2), -- 教師課程鐘點費率
    substitute_detail_id UUID, -- 代課明細表id (default null)，後面建立外鍵
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
    lessons_used INT DEFAULT 1, -- 學生使用堂數
    zoom_link TEXT, -- Zoom 連結
    zoom_meeting_id VARCHAR(100),
    zoom_password VARCHAR(50),
    recording_url TEXT, -- 錄影紀錄路徑
    recording_storage_path TEXT, -- AWS S3 路徑
    recording_duration_seconds INT,
    attendance_status VARCHAR(20) DEFAULT 'pending', -- present, absent, late
    teacher_notes TEXT, -- 教師備註
    student_feedback TEXT, -- 學生回饋
    rating INT CHECK (rating >= 1 AND rating <= 5), -- 評分
    
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
    substitute_hourly_rate DECIMAL(10,2), -- 代課教師鐘點費
    reason TEXT, -- 代課原因
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
    booking_id UUID REFERENCES bookings(id), -- 關聯的預約
    leave_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    reason TEXT NOT NULL,
    leave_status leave_status DEFAULT 'pending',
    approver_id UUID REFERENCES employees(id), -- 核准人ID
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
-- 21. 觸發器: 自動更新 updated_at
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 為所有表格建立觸發器
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

-- ============================================
-- 22. 視圖: 常用查詢視圖
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

-- ============================================
-- 23. RLS (Row Level Security) 政策範例
-- ============================================
-- 啟用 RLS
ALTER TABLE students ENABLE ROW LEVEL SECURITY;
ALTER TABLE teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE bookings ENABLE ROW LEVEL SECURITY;

-- 範例政策 (需根據實際 auth 設定調整)
-- CREATE POLICY "Students can view own data" ON students
--     FOR SELECT USING (auth.uid() = id);

-- CREATE POLICY "Teachers can view own data" ON teachers
--     FOR SELECT USING (auth.uid() = id);
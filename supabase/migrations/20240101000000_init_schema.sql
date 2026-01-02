-- ==========================================
-- 線上英文教學平台 - Supabase Schema
-- ==========================================

-- 啟用必要的擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ==========================================
-- 1. 基礎枚舉類型
-- ==========================================

CREATE TYPE user_role AS ENUM ('admin', 'teacher', 'student');
CREATE TYPE student_status AS ENUM ('trial', 'active', 'suspended', 'inactive');
CREATE TYPE teacher_status AS ENUM ('pending', 'active', 'suspended', 'inactive');
CREATE TYPE contract_status AS ENUM ('draft', 'active', 'expired', 'terminated');
CREATE TYPE booking_status AS ENUM ('scheduled', 'completed', 'cancelled', 'no_show');
CREATE TYPE payment_status AS ENUM ('pending', 'completed', 'failed', 'refunded');

-- ==========================================
-- 2. 使用者相關表格
-- ==========================================

-- 擴展 auth.users 的使用者資料表
CREATE TABLE public.user_profiles (
    id UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    role user_role NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(20),
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 3. 學生相關表格
-- ==========================================

-- 學生詳細資料
CREATE TABLE public.students (
    id UUID PRIMARY KEY REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    student_status student_status DEFAULT 'trial',
    trial_start_date DATE,
    trial_end_date DATE,
    formal_start_date DATE,
    emergency_contact VARCHAR(100),
    emergency_phone VARCHAR(20),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 學生合約
CREATE TABLE public.student_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    total_lessons INTEGER NOT NULL,
    remaining_lessons INTEGER NOT NULL,
    price_per_lesson DECIMAL(10, 2) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    status contract_status DEFAULT 'draft',
    contract_file_url TEXT,
    notes TEXT,
    created_by UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 課程包購買記錄
CREATE TABLE public.course_purchases (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    contract_id UUID REFERENCES public.student_contracts(id),
    package_name VARCHAR(100) NOT NULL,
    lesson_count INTEGER NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_status payment_status DEFAULT 'pending',
    payment_method VARCHAR(50),
    payment_date TIMESTAMP WITH TIME ZONE,
    invoice_url TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 4. 老師相關表格
-- ==========================================

-- 老師詳細資料
CREATE TABLE public.teachers (
    id UUID PRIMARY KEY REFERENCES public.user_profiles(id) ON DELETE CASCADE,
    teacher_status teacher_status DEFAULT 'pending',
    specialties TEXT[], -- 專長領域
    languages TEXT[], -- 語言能力
    hourly_rate DECIMAL(10, 2),
    bank_account VARCHAR(50),
    bank_name VARCHAR(100),
    tax_id VARCHAR(50),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 老師合約
CREATE TABLE public.teacher_contracts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES public.teachers(id) ON DELETE CASCADE,
    contract_number VARCHAR(50) UNIQUE NOT NULL,
    start_date DATE NOT NULL,
    end_date DATE,
    base_rate DECIMAL(10, 2) NOT NULL,
    commission_rate DECIMAL(5, 2), -- 抽成比例
    status contract_status DEFAULT 'draft',
    contract_file_url TEXT,
    notes TEXT,
    created_by UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 老師薪資記錄
CREATE TABLE public.teacher_payroll (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES public.teachers(id) ON DELETE CASCADE,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    total_lessons INTEGER NOT NULL,
    total_hours DECIMAL(10, 2) NOT NULL,
    base_amount DECIMAL(10, 2) NOT NULL,
    bonus_amount DECIMAL(10, 2) DEFAULT 0,
    deduction_amount DECIMAL(10, 2) DEFAULT 0,
    final_amount DECIMAL(10, 2) NOT NULL,
    payment_status payment_status DEFAULT 'pending',
    payment_date DATE,
    notes TEXT,
    created_by UUID REFERENCES public.user_profiles(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 5. Zoom 相關表格
-- ==========================================

-- Zoom 帳號管理
CREATE TABLE public.zoom_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_name VARCHAR(100) NOT NULL,
    zoom_user_id VARCHAR(100) NOT NULL UNIQUE,
    zoom_email VARCHAR(255) NOT NULL,
    api_key TEXT,
    api_secret TEXT,
    is_active BOOLEAN DEFAULT true,
    max_concurrent_meetings INTEGER DEFAULT 1,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ==========================================
-- 6. 課程預約與上課記錄
-- ==========================================

-- 課程預約
CREATE TABLE public.bookings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    student_id UUID NOT NULL REFERENCES public.students(id) ON DELETE CASCADE,
    teacher_id UUID NOT NULL REFERENCES public.teachers(id) ON DELETE CASCADE,
    contract_id UUID REFERENCES public.student_contracts(id),
    zoom_account_id UUID REFERENCES public.zoom_accounts(id),
    
    -- 課程時間
    scheduled_start TIMESTAMP WITH TIME ZONE NOT NULL,
    scheduled_end TIMESTAMP WITH TIME ZONE NOT NULL,
    actual_start TIMESTAMP WITH TIME ZONE,
    actual_end TIMESTAMP WITH TIME ZONE,
    
    -- Zoom 相關
    zoom_meeting_id VARCHAR(100),
    zoom_join_url TEXT,
    zoom_start_url TEXT,
    zoom_password VARCHAR(50),
    
    -- Google Calendar
    google_calendar_event_id VARCHAR(255),
    
    -- 錄影檔案
    recording_url TEXT,
    recording_password VARCHAR(50),
    recording_duration INTEGER, -- 分鐘
    
    -- 狀態與備註
    status booking_status DEFAULT 'scheduled',
    lesson_notes TEXT, -- 課程筆記
    student_feedback TEXT,
    teacher_feedback TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 課程出席記錄
CREATE TABLE public.attendance_records (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    booking_id UUID NOT NULL REFERENCES public.bookings(id) ON DELETE CASCADE,
    student_attended BOOLEAN,
    teacher_attended BOOLEAN,
    late_minutes INTEGER DEFAULT 0,
    early_leave_minutes INTEGER DEFAULT 0,
    technical_issues TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 啟用 btree_gist 擴展（用於排他約束）
CREATE EXTENSION IF NOT EXISTS btree_gist;

-- 建立排他約束，防止老師時段衝突
ALTER TABLE public.bookings 
ADD CONSTRAINT no_teacher_overlap 
EXCLUDE USING gist (
    teacher_id WITH =,
    tstzrange(scheduled_start, scheduled_end) WITH &&
) WHERE (status != 'cancelled');

-- ==========================================
-- 7. 索引優化
-- ==========================================

-- 學生相關索引
CREATE INDEX idx_students_status ON public.students(student_status);
CREATE INDEX idx_student_contracts_student ON public.student_contracts(student_id);
CREATE INDEX idx_student_contracts_status ON public.student_contracts(status);

-- 老師相關索引
CREATE INDEX idx_teachers_status ON public.teachers(teacher_status);
CREATE INDEX idx_teacher_contracts_teacher ON public.teacher_contracts(teacher_id);
CREATE INDEX idx_teacher_payroll_teacher ON public.teacher_payroll(teacher_id);

-- 預約相關索引
CREATE INDEX idx_bookings_student ON public.bookings(student_id);
CREATE INDEX idx_bookings_teacher ON public.bookings(teacher_id);
CREATE INDEX idx_bookings_status ON public.bookings(status);
CREATE INDEX idx_bookings_scheduled_start ON public.bookings(scheduled_start);
CREATE INDEX idx_bookings_date_range ON public.bookings(scheduled_start, scheduled_end);

-- ==========================================
-- 8. RLS (Row Level Security) 政策
-- ==========================================

-- 啟用 RLS
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.student_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.course_purchases ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teachers ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teacher_contracts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.teacher_payroll ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.zoom_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.attendance_records ENABLE ROW LEVEL SECURITY;

-- ==========================================
-- User Profiles RLS
-- ==========================================

-- Admin 可以查看所有人
CREATE POLICY "Admin can view all profiles" ON public.user_profiles
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- 使用者可以查看自己的資料
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

-- Admin 可以更新所有人
CREATE POLICY "Admin can update all profiles" ON public.user_profiles
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- 使用者可以更新自己的資料
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid());

-- ==========================================
-- Students RLS
-- ==========================================

-- Admin 可以查看所有學生
CREATE POLICY "Admin can view all students" ON public.students
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- 學生可以查看自己的資料
CREATE POLICY "Students can view own data" ON public.students
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

-- 老師可以查看已預約學生的資料
CREATE POLICY "Teachers can view booked students" ON public.students
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles up
            JOIN public.bookings b ON b.teacher_id = up.id
            WHERE up.id = auth.uid() 
            AND up.role = 'teacher'
            AND b.student_id = students.id
        )
    );

-- ==========================================
-- Student Contracts RLS
-- ==========================================

CREATE POLICY "Admin can manage all contracts" ON public.student_contracts
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Students can view own contracts" ON public.student_contracts
    FOR SELECT
    TO authenticated
    USING (student_id = auth.uid());

-- ==========================================
-- Teachers RLS
-- ==========================================

CREATE POLICY "Admin can view all teachers" ON public.teachers
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Teachers can view own data" ON public.teachers
    FOR SELECT
    TO authenticated
    USING (id = auth.uid());

CREATE POLICY "Students can view active teachers" ON public.teachers
    FOR SELECT
    TO authenticated
    USING (
        teacher_status = 'active' AND
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'student'
        )
    );

-- ==========================================
-- Teacher Payroll RLS
-- ==========================================

CREATE POLICY "Admin can manage payroll" ON public.teacher_payroll
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Teachers can view own payroll" ON public.teacher_payroll
    FOR SELECT
    TO authenticated
    USING (teacher_id = auth.uid());

-- ==========================================
-- Zoom Accounts RLS (只有 Admin 可以管理)
-- ==========================================

CREATE POLICY "Admin can manage zoom accounts" ON public.zoom_accounts
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

-- ==========================================
-- Bookings RLS
-- ==========================================

CREATE POLICY "Admin can manage all bookings" ON public.bookings
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Students can view own bookings" ON public.bookings
    FOR SELECT
    TO authenticated
    USING (student_id = auth.uid());

CREATE POLICY "Teachers can view own bookings" ON public.bookings
    FOR SELECT
    TO authenticated
    USING (teacher_id = auth.uid());

CREATE POLICY "Students can create bookings" ON public.bookings
    FOR INSERT
    TO authenticated
    WITH CHECK (student_id = auth.uid());

CREATE POLICY "Teachers can update own bookings" ON public.bookings
    FOR UPDATE
    TO authenticated
    USING (teacher_id = auth.uid());

-- ==========================================
-- Attendance Records RLS
-- ==========================================

CREATE POLICY "Admin can manage attendance" ON public.attendance_records
    FOR ALL
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles
            WHERE id = auth.uid() AND role = 'admin'
        )
    );

CREATE POLICY "Teachers and students can view related attendance" ON public.attendance_records
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.bookings b
            WHERE b.id = attendance_records.booking_id
            AND (b.student_id = auth.uid() OR b.teacher_id = auth.uid())
        )
    );

-- ==========================================
-- 9. 自動更新 updated_at 的觸發器
-- ==========================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_students_updated_at BEFORE UPDATE ON public.students
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_teachers_updated_at BEFORE UPDATE ON public.teachers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON public.bookings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ==========================================
-- 10. 實用的 View 和 Function
-- ==========================================

-- 學生課程餘額檢視
CREATE VIEW student_lesson_balance AS
SELECT 
    s.id as student_id,
    up.full_name,
    sc.id as contract_id,
    sc.contract_number,
    sc.total_lessons,
    sc.remaining_lessons,
    COUNT(b.id) FILTER (WHERE b.status = 'completed') as completed_lessons,
    sc.start_date,
    sc.end_date,
    sc.status as contract_status
FROM public.students s
JOIN public.user_profiles up ON up.id = s.id
LEFT JOIN public.student_contracts sc ON sc.student_id = s.id AND sc.status = 'active'
LEFT JOIN public.bookings b ON b.contract_id = sc.id
GROUP BY s.id, up.full_name, sc.id, sc.contract_number, sc.total_lessons, 
         sc.remaining_lessons, sc.start_date, sc.end_date, sc.status;

-- 老師課程統計檢視
CREATE VIEW teacher_lesson_stats AS
SELECT 
    t.id as teacher_id,
    up.full_name,
    COUNT(b.id) FILTER (WHERE b.status = 'completed') as total_completed,
    COUNT(b.id) FILTER (WHERE b.status = 'scheduled') as upcoming_lessons,
    SUM(EXTRACT(EPOCH FROM (b.actual_end - b.actual_start))/3600) as total_hours_taught
FROM public.teachers t
JOIN public.user_profiles up ON up.id = t.id
LEFT JOIN public.bookings b ON b.teacher_id = t.id
GROUP BY t.id, up.full_name;
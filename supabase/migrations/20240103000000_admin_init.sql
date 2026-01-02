-- ==========================================
-- 建立第一個 Admin 帳號（初始化時使用）
-- ==========================================

-- 方法 1: 直接在資料庫執行（僅在初始化時）
/*
-- 先在 Supabase Dashboard 建立一個使用者
-- 然後執行以下 SQL 將其升級為 admin

UPDATE public.user_profiles 
SET role = 'admin' 
WHERE email = 'your-admin@example.com';

DELETE FROM public.students 
WHERE id = (SELECT id FROM public.user_profiles WHERE email = 'your-admin@example.com');
*/

-- 方法 2: 透過環境變數設定初始 admin email
CREATE OR REPLACE FUNCTION public.initialize_first_admin()
RETURNS void AS $$
DECLARE
    admin_email TEXT := 'admin@example.com';  -- 改成你的 email
    admin_user_id UUID;
BEGIN
    -- 找到該 email 的使用者
    SELECT id INTO admin_user_id 
    FROM auth.users 
    WHERE email = admin_email;
    
    IF admin_user_id IS NOT NULL THEN
        -- 更新為 admin
        UPDATE public.user_profiles 
        SET role = 'admin' 
        WHERE id = admin_user_id;
        
        -- 移除 student 記錄
        DELETE FROM public.students WHERE id = admin_user_id;
        
        RAISE NOTICE 'First admin initialized: %', admin_email;
    ELSE
        RAISE NOTICE 'User not found: %', admin_email;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 執行初始化（只執行一次）
-- SELECT public.initialize_first_admin();

-- ==========================================
-- 審計日誌：記錄角色變更
-- ==========================================

CREATE TABLE IF NOT EXISTS public.role_change_audit (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES public.user_profiles(id),
    old_role user_role,
    new_role user_role,
    changed_by UUID REFERENCES public.user_profiles(id),
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    reason TEXT
);

-- 修改 admin_change_user_role 函式，加入審計日誌
CREATE OR REPLACE FUNCTION public.admin_change_user_role(
    target_user_id UUID,
    new_role user_role,
    reason TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
DECLARE
    old_role user_role;
BEGIN
    -- 🔒 檢查呼叫者是否為 admin
    IF NOT EXISTS (
        SELECT 1 FROM public.user_profiles 
        WHERE id = auth.uid() AND role = 'admin'
    ) THEN
        RAISE EXCEPTION 'Only admins can change user roles';
    END IF;
    
    -- 取得舊角色
    SELECT role INTO old_role FROM public.user_profiles WHERE id = target_user_id;
    
    -- 記錄審計日誌
    INSERT INTO public.role_change_audit (user_id, old_role, new_role, changed_by, reason)
    VALUES (target_user_id, old_role, new_role, auth.uid(), reason);
    
    -- 更新角色
    UPDATE public.user_profiles 
    SET role = new_role, updated_at = NOW()
    WHERE id = target_user_id;
    
    -- 處理角色相關的表格記錄（同上）
    IF old_role = 'student' AND new_role != 'student' THEN
        DELETE FROM public.students WHERE id = target_user_id;
    END IF;
    
    IF old_role = 'teacher' AND new_role != 'teacher' THEN
        DELETE FROM public.teachers WHERE id = target_user_id;
    END IF;
    
    IF new_role = 'student' AND old_role != 'student' THEN
        INSERT INTO public.students (id, student_status) 
        VALUES (target_user_id, 'trial')
        ON CONFLICT (id) DO NOTHING;
    END IF;
    
    IF new_role = 'teacher' AND old_role != 'teacher' THEN
        INSERT INTO public.teachers (id, teacher_status) 
        VALUES (target_user_id, 'pending')
        ON CONFLICT (id) DO NOTHING;
    END IF;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 審計日誌的 RLS
ALTER TABLE public.role_change_audit ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Admin can view audit logs" ON public.role_change_audit
    FOR SELECT
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );
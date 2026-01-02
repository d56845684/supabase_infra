-- ==========================================
-- 安全的自動建立 User Profile 觸發器
-- ==========================================

-- ⚠️ 安全方案：防止前端任意指定角色
-- 預設所有註冊都是 student，只有 admin 能升級權限

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER 
SECURITY DEFINER 
SET search_path = public
AS $$
BEGIN
    INSERT INTO public.user_profiles (id, role, full_name, email, phone, avatar_url)
    VALUES (
        NEW.id,
        'student'::user_role,
        COALESCE(
            NEW.raw_user_meta_data->>'full_name',
            NEW.raw_user_meta_data->>'name',
            SPLIT_PART(NEW.email, '@', 1),
            ''
        ),
        COALESCE(NEW.email, ''),
        NEW.raw_user_meta_data->>'phone',
        NEW.raw_user_meta_data->>'avatar_url'
    )
    ON CONFLICT (id) DO NOTHING;

    INSERT INTO public.students (id, student_status)
    VALUES (NEW.id, 'trial')
    ON CONFLICT (id) DO NOTHING;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 建立觸發器
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_new_user();

-- ==========================================
-- 角色管理：只有 Admin 能建立和變更角色
-- ==========================================

-- 建立管理員專用的函式來建立老師帳號
CREATE OR REPLACE FUNCTION public.admin_create_teacher(
    teacher_email TEXT,
    teacher_password TEXT,
    teacher_full_name TEXT,
    teacher_phone TEXT DEFAULT NULL
)
RETURNS JSON AS $$
DECLARE
    new_user_id UUID;
    result JSON;
BEGIN
    -- 🔒 檢查呼叫者是否為 admin
    IF NOT EXISTS (
        SELECT 1 FROM public.user_profiles 
        WHERE id = auth.uid() AND role = 'admin'
    ) THEN
        RAISE EXCEPTION 'Only admins can create teacher accounts';
    END IF;
    
    -- 使用 Supabase Admin API 建立使用者（需要在 Edge Function 中執行）
    -- 這裡提供邏輯，實際執行在 Edge Function
    
    RETURN json_build_object(
        'success', true,
        'message', 'Teacher account creation initiated'
    );
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 建立管理員專用的函式來變更使用者角色
CREATE OR REPLACE FUNCTION public.admin_change_user_role(
    target_user_id UUID,
    new_role user_role
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
    
    -- 🔒 防止刪除最後一個 admin
    IF new_role != 'admin' THEN
        IF (SELECT COUNT(*) FROM public.user_profiles WHERE role = 'admin') <= 1 
           AND (SELECT role FROM public.user_profiles WHERE id = target_user_id) = 'admin' THEN
            RAISE EXCEPTION 'Cannot remove the last admin';
        END IF;
    END IF;
    
    -- 取得舊角色
    SELECT role INTO old_role FROM public.user_profiles WHERE id = target_user_id;
    
    -- 更新角色
    UPDATE public.user_profiles 
    SET role = new_role, updated_at = NOW()
    WHERE id = target_user_id;
    
    -- 根據角色變更，建立或刪除對應的記錄
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

-- ==========================================
-- RLS 政策：防止角色欄位被竄改
-- ==========================================

-- 防止使用者自行修改 role 欄位
CREATE POLICY "Users cannot change their own role" ON public.user_profiles
    FOR UPDATE
    TO authenticated
    USING (id = auth.uid())
    WITH CHECK (
        -- 只能更新自己的資料，且不能改 role
        id = auth.uid() AND 
        role = (SELECT role FROM public.user_profiles WHERE id = auth.uid())
    );

-- Admin 可以修改任何人的 role
CREATE POLICY "Admin can change any role" ON public.user_profiles
    FOR UPDATE
    TO authenticated
    USING (
        EXISTS (
            SELECT 1 FROM public.user_profiles 
            WHERE id = auth.uid() AND role = 'admin'
        )
    );
-- user_profiles INSERT 政策
CREATE POLICY "Service role can insert profiles" ON public.user_profiles
    FOR INSERT TO service_role WITH CHECK (true);

-- students INSERT 政策  
CREATE POLICY "Service role can insert students" ON public.students
    FOR INSERT TO service_role WITH CHECK (true);
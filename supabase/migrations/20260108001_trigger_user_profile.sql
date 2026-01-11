-- 建立觸發器函數：註冊時補齊對應實體 ID
CREATE OR REPLACE FUNCTION create_user_entity()
RETURNS TRIGGER AS $$
BEGIN
    -- 根據角色補齊對應實體 ID（需與 auth.users id 一致）
    CASE NEW.role
        WHEN 'student' THEN
            NEW.student_id := NEW.id;
        WHEN 'teacher' THEN
            NEW.teacher_id := NEW.id;
        WHEN 'employee', 'admin' THEN
            NEW.employee_id := NEW.id;
    END CASE;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- 建立觸發器
DROP TRIGGER IF EXISTS trg_create_user_entity ON user_profiles;
CREATE TRIGGER trg_create_user_entity
    BEFORE INSERT ON user_profiles
    FOR EACH ROW
    WHEN (
        (NEW.role = 'student' AND NEW.student_id IS NULL) OR
        (NEW.role = 'teacher' AND NEW.teacher_id IS NULL) OR
        (NEW.role IN ('employee', 'admin') AND NEW.employee_id IS NULL)
    )
    EXECUTE FUNCTION create_user_entity();

-- 建立觸發器函數：註冊時自動建立 user_profiles
CREATE OR REPLACE FUNCTION create_user_profile_from_auth()
RETURNS TRIGGER AS $$
DECLARE
    v_role TEXT;
BEGIN
    v_role := COALESCE(NEW.raw_user_meta_data->>'role', 'student');

    INSERT INTO user_profiles (
        id,
        role,
        student_id,
        teacher_id,
        employee_id
    )
    VALUES (
        NEW.id,
        v_role::user_role,
        CASE WHEN v_role = 'student' THEN NEW.id ELSE NULL END,
        CASE WHEN v_role = 'teacher' THEN NEW.id ELSE NULL END,
        CASE WHEN v_role IN ('employee', 'admin') THEN NEW.id ELSE NULL END
    );

    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trg_create_user_profile ON auth.users;
CREATE TRIGGER trg_create_user_profile
    AFTER INSERT ON auth.users
    FOR EACH ROW
    EXECUTE FUNCTION create_user_profile_from_auth();

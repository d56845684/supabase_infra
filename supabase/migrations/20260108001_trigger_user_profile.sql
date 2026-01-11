-- 建立觸發器函數：註冊時從 auth.users metadata 寫入對應實體 ID
CREATE OR REPLACE FUNCTION create_user_entity()
RETURNS TRIGGER AS $$
BEGIN
    -- 根據角色從 auth.users metadata 帶入對應實體 ID
    CASE NEW.role
        WHEN 'student' THEN
            NEW.student_id := NULLIF(
                (SELECT raw_user_meta_data->>'student_id' FROM auth.users WHERE id = NEW.id),
                ''
            )::UUID;
        WHEN 'teacher' THEN
            NEW.teacher_id := NULLIF(
                (SELECT raw_user_meta_data->>'teacher_id' FROM auth.users WHERE id = NEW.id),
                ''
            )::UUID;
        WHEN 'employee', 'admin' THEN
            NEW.employee_id := NULLIF(
                (SELECT raw_user_meta_data->>'employee_id' FROM auth.users WHERE id = NEW.id),
                ''
            )::UUID;
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

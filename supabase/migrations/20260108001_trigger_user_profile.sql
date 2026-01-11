-- 建立觸發器函數：註冊時自動建立對應實體
CREATE OR REPLACE FUNCTION create_user_entity()
RETURNS TRIGGER AS $$
DECLARE
    v_entity_id UUID;
BEGIN
    -- 根據角色建立對應實體
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
                NEW.role,
                CURRENT_DATE,
                TRUE
            )
            RETURNING id INTO v_entity_id;
            NEW.employee_id := v_entity_id;
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
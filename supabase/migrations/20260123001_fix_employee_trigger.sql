-- Fix: Update trigger to use employee_subtype for employee_type
-- Previously, the trigger used NEW.role ('employee') which is not a valid employee_type enum value

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

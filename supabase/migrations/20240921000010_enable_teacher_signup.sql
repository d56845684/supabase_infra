-- Allow teacher or student self-registration without email verification by default
-- but keep the trigger extensible for future verification flows.
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    requested_role user_role := 'student';
    requested_role_text TEXT := lower(COALESCE(NEW.raw_user_meta_data->>'requested_role', ''));
BEGIN
    IF requested_role_text IN ('teacher', 'student') THEN
        requested_role := requested_role_text::user_role;
    END IF;

    INSERT INTO public.user_profiles (id, role, full_name, email, phone, avatar_url)
    VALUES (
        NEW.id,
        requested_role,
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

    IF requested_role = 'teacher' THEN
        INSERT INTO public.teachers (id, teacher_status)
        VALUES (NEW.id, 'pending')
        ON CONFLICT (id) DO NOTHING;
    ELSE
        INSERT INTO public.students (id, student_status)
        VALUES (NEW.id, 'trial')
        ON CONFLICT (id) DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

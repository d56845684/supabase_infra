-- Booking management view and available slot enforcement

-- helper table to track admin ids without recursive user_profiles lookups
CREATE TABLE IF NOT EXISTS public.admin_accounts (
    user_id UUID PRIMARY KEY
);

INSERT INTO public.admin_accounts (user_id)
SELECT id
FROM public.user_profiles
WHERE role = 'admin' AND deleted_at IS NULL
ON CONFLICT DO NOTHING;

CREATE OR REPLACE FUNCTION public.sync_admin_accounts()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
    IF NEW.role = 'admin' AND NEW.deleted_at IS NULL THEN
        INSERT INTO public.admin_accounts(user_id)
        VALUES (NEW.id)
        ON CONFLICT (user_id) DO NOTHING;
    ELSE
        DELETE FROM public.admin_accounts WHERE user_id = NEW.id;
    END IF;
    RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS trg_sync_admin_accounts ON public.user_profiles;
CREATE TRIGGER trg_sync_admin_accounts
AFTER INSERT OR UPDATE ON public.user_profiles
FOR EACH ROW
EXECUTE FUNCTION public.sync_admin_accounts();

CREATE OR REPLACE FUNCTION public.is_admin(uid UUID DEFAULT auth.uid())
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
SET search_path = public
AS $$
    SELECT EXISTS (
        SELECT 1 FROM public.admin_accounts a WHERE a.user_id = uid
    );
$$;

REVOKE ALL ON FUNCTION public.is_admin(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_admin(UUID) TO authenticated;

DROP POLICY IF EXISTS "Admin can view all profiles" ON public.user_profiles;
CREATE POLICY "Admin can view all profiles" ON public.user_profiles
    FOR SELECT TO authenticated
    USING (public.is_admin());

DROP POLICY IF EXISTS "Admin can update all profiles" ON public.user_profiles;
CREATE POLICY "Admin can update all profiles" ON public.user_profiles
    FOR UPDATE TO authenticated
    USING (public.is_admin());

-- Available slots for teachers that students can book into
CREATE TABLE IF NOT EXISTS public.teacher_available_slots (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    teacher_id UUID NOT NULL REFERENCES public.teachers(id) ON DELETE CASCADE,
    slot_start TIMESTAMPTZ NOT NULL,
    slot_end TIMESTAMPTZ NOT NULL,
    is_open BOOLEAN DEFAULT TRUE,
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE public.teacher_available_slots
    ADD CONSTRAINT no_teacher_slot_overlap EXCLUDE USING gist (
        teacher_id WITH =,
        tstzrange(slot_start, slot_end) WITH &&
    ) WHERE (is_open);

ALTER TABLE public.teacher_available_slots ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Admins manage slots" ON public.teacher_available_slots;
CREATE POLICY "Admins manage slots" ON public.teacher_available_slots
    FOR ALL TO authenticated
    USING (public.is_admin());

DROP POLICY IF EXISTS "Teachers manage own slots" ON public.teacher_available_slots;
CREATE POLICY "Teachers manage own slots" ON public.teacher_available_slots
    FOR ALL TO authenticated
    USING (teacher_id = auth.uid());

DROP POLICY IF EXISTS "Students can view open slots" ON public.teacher_available_slots;
CREATE POLICY "Students can view open slots" ON public.teacher_available_slots
    FOR SELECT TO authenticated
    USING (is_open);

CREATE TRIGGER trg_teacher_slots_updated_at
BEFORE UPDATE ON public.teacher_available_slots
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();

-- bookings must map to a defined slot for students
ALTER TABLE public.bookings
ADD COLUMN IF NOT EXISTS slot_id UUID REFERENCES public.teacher_available_slots(id);

DROP VIEW IF EXISTS public.v_booking_management;
CREATE VIEW public.v_booking_management AS
SELECT
    b.id,
    b.student_id,
    b.teacher_id,
    b.slot_id,
    b.scheduled_start,
    b.scheduled_end,
    b.actual_start,
    b.actual_end,
    b.status,
    b.lesson_notes,
    b.student_feedback,
    b.teacher_feedback,
    b.contract_id,
    b.zoom_account_id,
    b.zoom_meeting_id,
    b.zoom_join_url,
    b.zoom_start_url,
    b.zoom_password,
    b.google_calendar_event_id,
    b.recording_url,
    b.recording_password,
    b.recording_duration,
    b.created_at,
    b.updated_at,
    sup.full_name AS student_name,
    sup.email AS student_email,
    tup.full_name AS teacher_name,
    tup.email AS teacher_email,
    tas.slot_start,
    tas.slot_end,
    tas.is_open AS slot_is_open
FROM public.bookings b
LEFT JOIN public.user_profiles sup ON sup.id = b.student_id
LEFT JOIN public.user_profiles tup ON tup.id = b.teacher_id
LEFT JOIN public.teacher_available_slots tas ON tas.id = b.slot_id
WHERE b.deleted_at IS NULL
  AND (
    public.is_admin()
    OR b.student_id = auth.uid()
    OR b.teacher_id = auth.uid()
  );

ALTER VIEW public.v_booking_management SET (security_barrier = true);
ALTER VIEW public.v_booking_management OWNER TO postgres;
REVOKE ALL ON public.v_booking_management FROM PUBLIC;
GRANT SELECT ON public.v_booking_management TO authenticated;

-- tighten booking insert for students to only open slots
DROP POLICY IF EXISTS "Students can create bookings" ON public.bookings;
CREATE POLICY "Students can create bookings" ON public.bookings
    FOR INSERT TO authenticated
    WITH CHECK (
        student_id = auth.uid()
        AND slot_id IS NOT NULL
        AND EXISTS (
            SELECT 1
            FROM public.teacher_available_slots tas
            WHERE tas.id = bookings.slot_id
              AND tas.teacher_id = bookings.teacher_id
              AND tas.is_open
              AND bookings.scheduled_start >= tas.slot_start
              AND bookings.scheduled_end <= tas.slot_end
        )
    );

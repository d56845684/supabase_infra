-- Enhance teacher available slots visibility and conflict rules
ALTER TABLE public.teacher_available_slots
  ADD COLUMN IF NOT EXISTS visible_to_all BOOLEAN DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS visible_student_ids UUID[] DEFAULT '{}'::UUID[];

-- Strengthen overlap prevention to honor blocking slots
ALTER TABLE public.teacher_available_slots
  DROP CONSTRAINT IF EXISTS no_teacher_slot_overlap;

ALTER TABLE public.teacher_available_slots
  ADD CONSTRAINT no_teacher_slot_overlap EXCLUDE USING gist (
    teacher_id WITH =,
    tstzrange(slot_start, slot_end) WITH &&
  );

-- Update visibility policy for students
DROP POLICY IF EXISTS "Students can view open slots" ON public.teacher_available_slots;
CREATE POLICY "Students can view open slots" ON public.teacher_available_slots
  FOR SELECT TO authenticated
  USING (
    is_open
    AND (
      visible_to_all
      OR auth.uid() = ANY(visible_student_ids)
    )
  );

-- Allow admins and teachers to manage visibility fields
DROP POLICY IF EXISTS "Admins manage slots" ON public.teacher_available_slots;
CREATE POLICY "Admins manage slots" ON public.teacher_available_slots
  FOR ALL TO authenticated
  USING (public.is_admin());

DROP POLICY IF EXISTS "Teachers manage own slots" ON public.teacher_available_slots;
CREATE POLICY "Teachers manage own slots" ON public.teacher_available_slots
  FOR ALL TO authenticated
  USING (teacher_id = auth.uid());

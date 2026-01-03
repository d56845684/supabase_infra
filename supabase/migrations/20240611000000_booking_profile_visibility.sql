-- Convert to ALTER policy so the definition can be updated without recreation
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_policies
        WHERE policyname = 'Booking participants can view related profiles'
          AND schemaname = 'public'
          AND tablename = 'user_profiles'
    ) THEN
        CREATE POLICY "Booking participants can view related profiles" ON public.user_profiles
            FOR SELECT
            TO authenticated
            USING (
                id = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM public.bookings b
                    WHERE (b.student_id = auth.uid() OR b.teacher_id = auth.uid())
                      AND (b.student_id = user_profiles.id OR b.teacher_id = user_profiles.id)
                )
            );
    ELSE
        ALTER POLICY "Booking participants can view related profiles" ON public.user_profiles
            USING (
                id = auth.uid()
                OR EXISTS (
                    SELECT 1 FROM public.bookings b
                    WHERE (b.student_id = auth.uid() OR b.teacher_id = auth.uid())
                      AND (b.student_id = user_profiles.id OR b.teacher_id = user_profiles.id)
                )
            );
    END IF;
END$$;

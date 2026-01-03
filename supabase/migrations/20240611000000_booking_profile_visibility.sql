-- Allow booking participants to see the profiles of teachers and students involved in their bookings
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

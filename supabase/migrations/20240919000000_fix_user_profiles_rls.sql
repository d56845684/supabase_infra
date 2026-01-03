-- ==========================================
-- Fix user_profiles RLS recursion by using a definer helper
-- ==========================================

-- Helper function to check admin role without triggering RLS recursion
CREATE OR REPLACE FUNCTION public.is_admin(uid UUID DEFAULT auth.uid())
RETURNS BOOLEAN
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    user_is_admin BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1
        FROM public.user_profiles
        WHERE id = uid
          AND role = 'admin'
          AND deleted_at IS NULL
    ) INTO user_is_admin;

    RETURN COALESCE(user_is_admin, FALSE);
END;
$$;

REVOKE ALL ON FUNCTION public.is_admin(UUID) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.is_admin(UUID) TO authenticated;

-- Refresh user_profiles policies to rely on the helper
DROP POLICY IF EXISTS "Admin can view all profiles" ON public.user_profiles;
CREATE POLICY "Admin can view all profiles" ON public.user_profiles
    FOR SELECT TO authenticated
    USING (public.is_admin());

DROP POLICY IF EXISTS "Users can view own profile" ON public.user_profiles;
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT TO authenticated
    USING (id = auth.uid() AND deleted_at IS NULL);

DROP POLICY IF EXISTS "Admin can update all profiles" ON public.user_profiles;
CREATE POLICY "Admin can update all profiles" ON public.user_profiles
    FOR UPDATE TO authenticated
    USING (public.is_admin());

DROP POLICY IF EXISTS "Users can update own profile" ON public.user_profiles;
CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE TO authenticated
    USING (id = auth.uid() AND deleted_at IS NULL);

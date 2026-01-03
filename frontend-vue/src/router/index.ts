import { createRouter, createWebHistory, NavigationGuardNext, RouteLocationNormalized } from 'vue-router';
import SystemAccounts from '@/views/system/SystemAccounts.vue';
import RoleManagement from '@/views/system/RoleManagement.vue';
import Payroll from '@/views/system/Payroll.vue';
import TeacherLeave from '@/views/system/TeacherLeave.vue';
import TeacherManagement from '@/views/courses/TeacherManagement.vue';
import TeacherAccounts from '@/views/courses/TeacherAccounts.vue';
import TeacherOverview from '@/views/courses/TeacherOverview.vue';
import StudentBookings from '@/views/students/StudentBookings.vue';
import LoginView from '@/views/auth/LoginView.vue';
import RegisterView from '@/views/auth/RegisterView.vue';
import { useAuthStore } from '@/stores/auth';
import { useDataStore } from '@/stores/dataStore';
import type { UserRole } from '@/types/schema';

const routes = [
  { path: '/', redirect: '/login' },
  { path: '/login', component: LoginView, meta: { public: true } },
  { path: '/register', component: RegisterView, meta: { public: true } },
  { path: '/system/accounts', component: SystemAccounts, meta: { roles: ['admin'] satisfies UserRole[] } },
  { path: '/system/roles', component: RoleManagement, meta: { roles: ['admin'] satisfies UserRole[] } },
  { path: '/system/payroll', component: Payroll, meta: { roles: ['admin'] satisfies UserRole[] } },
  { path: '/system/leave', component: TeacherLeave, meta: { roles: ['admin', 'teacher'] satisfies UserRole[] } },
  { path: '/courses/teachers', component: TeacherManagement, meta: { roles: ['admin', 'teacher'] satisfies UserRole[] } },
  { path: '/courses/teacher-accounts', component: TeacherAccounts, meta: { roles: ['admin', 'teacher'] satisfies UserRole[] } },
  { path: '/courses/overview', component: TeacherOverview, meta: { roles: ['admin', 'teacher'] satisfies UserRole[] } },
  { path: '/students/bookings', component: StudentBookings, meta: { roles: ['admin', 'teacher', 'student'] satisfies UserRole[] } }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

async function guardLoggedIn(to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) {
  const auth = useAuthStore();
  const dataStore = useDataStore();

  if (to.meta.public) {
    await auth.restoreSession();
    if (auth.currentUser && ['/login', '/register'].includes(to.path)) {
      return next(auth.defaultRoute);
    }
    return next();
  }

  await auth.restoreSession();
  if (!auth.currentUser) {
    return next({ path: '/login', query: { redirect: to.fullPath } });
  }

  try {
    await dataStore.ensureInitialized();
  } catch (error) {
    console.error('Failed to sync Supabase state', error);
  }

  const allowedRoles = to.meta.roles as UserRole[] | undefined;
  if (!auth.canAccessRole(auth.currentUser.role, allowedRoles)) {
    return next(auth.defaultRoute);
  }

  return next();
}

router.beforeEach(guardLoggedIn);

export default router;

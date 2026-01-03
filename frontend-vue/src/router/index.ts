import { createRouter, createWebHistory, NavigationGuardNext, RouteLocationNormalized } from 'vue-router';
import SystemAccounts from '@/views/system/SystemAccounts.vue';
import RoleManagement from '@/views/system/RoleManagement.vue';
import Payroll from '@/views/system/Payroll.vue';
import TeacherLeave from '@/views/system/TeacherLeave.vue';
import TeacherManagement from '@/views/courses/TeacherManagement.vue';
import TeacherAccounts from '@/views/courses/TeacherAccounts.vue';
import TeacherOverview from '@/views/courses/TeacherOverview.vue';
import StudentBookings from '@/views/students/StudentBookings.vue';
import { useAuthStore } from '@/stores/auth';

const routes = [
  { path: '/', redirect: '/system/accounts' },
  { path: '/system/accounts', component: SystemAccounts },
  { path: '/system/roles', component: RoleManagement },
  { path: '/system/payroll', component: Payroll },
  { path: '/system/leave', component: TeacherLeave },
  { path: '/courses/teachers', component: TeacherManagement },
  { path: '/courses/teacher-accounts', component: TeacherAccounts },
  { path: '/courses/overview', component: TeacherOverview },
  { path: '/students/bookings', component: StudentBookings }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

function guardLoggedIn(to: RouteLocationNormalized, from: RouteLocationNormalized, next: NavigationGuardNext) {
  const auth = useAuthStore();
  if (!auth.currentUser) {
    auth.autoLogin();
  }
  next();
}

router.beforeEach(guardLoggedIn);

export default router;

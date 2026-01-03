<template>
  <div v-if="isAuthRoute" class="auth-shell">
    <router-view />
  </div>
  <div v-else :class="themeClass" class="app-shell">
    <el-container>
      <el-header class="app-header">
        <div class="logo-area">Teaching Admin</div>
        <div class="header-actions">
          <div v-if="authStore.currentUser" class="user-meta">
            <div class="user-name">{{ authStore.currentUser.full_name }}</div>
            <div class="user-role">{{ $t(`auth.roles.${authStore.currentUser.role}`) }}</div>
          </div>
          <el-switch
            v-model="isDark"
            :active-text="$t('theme.dark')"
            :inactive-text="$t('theme.light')"
            @change="toggleTheme"
          />
          <el-select v-model="locale" size="small" @change="changeLocale">
            <el-option label="English" value="en" />
            <el-option label="繁體中文" value="zh-TW" />
          </el-select>
          <el-button type="primary" size="small" @click="onLogout">{{ $t('auth.logout') }}</el-button>
        </div>
      </el-header>
      <el-container>
        <el-aside width="240px" class="app-aside">
          <el-menu :default-active="activePath" router>
            <el-sub-menu v-if="hasSystemMenu" index="system">
              <template #title>{{ $t('nav.system') }}</template>
              <el-menu-item v-if="canAccessRoute('/system/accounts')" index="/system/accounts">
                {{ $t('nav.backendAccounts') }}
              </el-menu-item>
              <el-menu-item v-if="canAccessRoute('/system/roles')" index="/system/roles">{{ $t('nav.roles') }}</el-menu-item>
              <el-menu-item v-if="canAccessRoute('/system/payroll')" index="/system/payroll">
                {{ $t('nav.payroll') }}
              </el-menu-item>
              <el-menu-item v-if="canAccessRoute('/system/leave')" index="/system/leave">
                {{ $t('nav.teacherLeave') }}
              </el-menu-item>
            </el-sub-menu>
            <el-sub-menu v-if="hasCourseMenu" index="courses">
              <template #title>{{ $t('nav.courses') }}</template>
              <el-menu-item v-if="canAccessRoute('/courses/teachers')" index="/courses/teachers">
                {{ $t('nav.teacherProfiles') }}
              </el-menu-item>
              <el-menu-item v-if="canAccessRoute('/courses/teacher-accounts')" index="/courses/teacher-accounts">
                {{ $t('nav.teacherAccounts') }}
              </el-menu-item>
              <el-menu-item v-if="canAccessRoute('/courses/overview')" index="/courses/overview">
                {{ $t('nav.bookingOverview') }}
              </el-menu-item>
            </el-sub-menu>
            <el-sub-menu v-if="hasStudentMenu" index="students">
              <template #title>{{ $t('nav.students') }}</template>
              <el-menu-item v-if="canAccessRoute('/students/bookings')" index="/students/bookings">
                {{ $t('nav.studentBookings') }}
              </el-menu-item>
            </el-sub-menu>
          </el-menu>
        </el-aside>
        <el-main>
          <router-view />
        </el-main>
      </el-container>
    </el-container>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from './stores/auth';
import { useThemeStore } from './stores/theme';
import { useInactivityLogout } from './composables/useInactivityLogout';
import { useI18n } from 'vue-i18n';

const route = useRoute();
const router = useRouter();
const themeStore = useThemeStore();
const authStore = useAuthStore();
const { locale: i18nLocale } = useI18n();

const isDark = computed({
  get: () => themeStore.isDark,
  set: (val) => themeStore.setDark(val)
});

const themeClass = computed(() => (isDark.value ? 'dark' : 'light'));
const activePath = computed(() => route.path);
const locale = ref<string>(i18nLocale.value as string);
const isAuthRoute = computed(() => route.meta.public === true);

const canAccessRoute = (path: string) => {
  const matched = router.getRoutes().find((r) => r.path === path);
  const roles = matched?.meta.roles as string[] | undefined;
  const userRole = authStore.currentUser?.role;
  if (!roles || roles.length === 0) return true;
  return roles.includes(userRole ?? '');
};

const hasSystemMenu = computed(() =>
  ['/system/accounts', '/system/roles', '/system/payroll', '/system/leave'].some((path) => canAccessRoute(path))
);
const hasCourseMenu = computed(() =>
  ['/courses/teachers', '/courses/teacher-accounts', '/courses/overview'].some((path) => canAccessRoute(path))
);
const hasStudentMenu = computed(() => ['/students/bookings'].some((path) => canAccessRoute(path)));

const { resetTimer } = useInactivityLogout({
  onTimeout: async () => {
    await authStore.logout();
    router.push('/login');
  }
});

watch(
  () => route.fullPath,
  () => resetTimer()
);

const toggleTheme = () => themeStore.toggleTheme();
const changeLocale = (value: string) => {
  i18nLocale.value = value;
};
const onLogout = async () => {
  await authStore.logout();
  router.push('/login');
};
</script>

<style scoped>
.auth-shell {
  min-height: 100vh;
}

.app-shell {
  min-height: 100vh;
  background: var(--el-bg-color);
  color: var(--el-text-color-primary);
}

.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 24px;
  border-bottom: 1px solid var(--el-border-color);
}

.logo-area {
  font-weight: 700;
  font-size: 18px;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.user-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  margin-right: 8px;
  font-size: 12px;
}

.user-name {
  font-weight: 600;
}

.user-role {
  color: var(--el-text-color-secondary);
}

.app-aside {
  border-right: 1px solid var(--el-border-color);
  min-height: calc(100vh - 64px);
}
</style>

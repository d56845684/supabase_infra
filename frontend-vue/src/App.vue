<template>
  <div :class="themeClass" class="app-shell">
    <el-container>
      <el-header class="app-header">
        <div class="logo-area">Teaching Admin</div>
        <div class="header-actions">
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
            <el-sub-menu index="system">
              <template #title>{{ $t('nav.system') }}</template>
              <el-menu-item index="/system/accounts">{{ $t('nav.backendAccounts') }}</el-menu-item>
              <el-menu-item index="/system/roles">{{ $t('nav.roles') }}</el-menu-item>
              <el-menu-item index="/system/payroll">{{ $t('nav.payroll') }}</el-menu-item>
              <el-menu-item index="/system/leave">{{ $t('nav.teacherLeave') }}</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="courses">
              <template #title>{{ $t('nav.courses') }}</template>
              <el-menu-item index="/courses/teachers">{{ $t('nav.teacherProfiles') }}</el-menu-item>
              <el-menu-item index="/courses/teacher-accounts">{{ $t('nav.teacherAccounts') }}</el-menu-item>
              <el-menu-item index="/courses/overview">{{ $t('nav.bookingOverview') }}</el-menu-item>
            </el-sub-menu>
            <el-sub-menu index="students">
              <template #title>{{ $t('nav.students') }}</template>
              <el-menu-item index="/students/bookings">{{ $t('nav.studentBookings') }}</el-menu-item>
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

const { resetTimer } = useInactivityLogout({
  onTimeout: async () => {
    await authStore.logout();
    router.push('/system/accounts');
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
  router.push('/system/accounts');
};
</script>

<style scoped>
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

.app-aside {
  border-right: 1px solid var(--el-border-color);
  min-height: calc(100vh - 64px);
}
</style>

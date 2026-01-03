<template>
  <div class="auth-layout">
    <div class="auth-card">
      <div class="auth-header">
        <h1>{{ $t('auth.registerTitle') }}</h1>
        <p>{{ $t('auth.registerSubtitle') }}</p>
      </div>
      <el-tabs v-model="activeTab" class="role-tabs">
        <el-tab-pane :label="$t('auth.roles.student')" name="student">
          <RegistrationForm
            role="student"
            :loading="loading"
            :error="error"
            :success="success"
            :email-verification-enabled="emailVerificationEnabled"
            @submit="onSubmit"
          />
        </el-tab-pane>
        <el-tab-pane :label="$t('auth.roles.teacher')" name="teacher">
          <RegistrationForm
            role="teacher"
            :loading="loading"
            :error="error"
            :success="success"
            :email-verification-enabled="emailVerificationEnabled"
            @submit="onSubmit"
          />
        </el-tab-pane>
      </el-tabs>
      <div class="footer-actions">
        <span>{{ $t('auth.haveAccount') }}</span>
        <router-link to="/login">{{ $t('auth.backToLogin') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
import { useRouter } from 'vue-router';
import { useI18n } from 'vue-i18n';
import RegistrationForm from './components/RegistrationForm.vue';
import { useAuthStore } from '@/stores/auth';
import type { UserRole } from '@/types/schema';

const router = useRouter();
const auth = useAuthStore();
const { t } = useI18n();

const activeTab = ref<UserRole>('student');
const loading = ref(false);
const error = ref('');
const success = ref('');

const emailVerificationEnabled = computed(() => import.meta.env.VITE_ENABLE_EMAIL_VERIFICATION === 'true');
const emailRedirectTo = computed(() => import.meta.env.VITE_EMAIL_REDIRECT_TO as string | undefined);

const onSubmit = async (payload: {
  fullName: string;
  email: string;
  password: string;
  phone?: string;
  role: UserRole;
}) => {
  error.value = '';
  success.value = '';
  loading.value = true;
  try {
    await auth.registerWithEmail({
      ...payload,
      requireEmailVerification: emailVerificationEnabled.value,
      emailRedirectTo: emailRedirectTo.value
    });
    if (emailVerificationEnabled.value) {
      success.value = t('auth.registerCheckEmail');
    } else {
      success.value = t('auth.registerSuccess');
      router.push(auth.defaultRoute);
    }
  } catch (err) {
    if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = t('auth.registerError');
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(circle at 10% 20%, rgba(99, 102, 241, 0.2), transparent 25%),
    radial-gradient(circle at 90% 30%, rgba(16, 185, 129, 0.2), transparent 25%),
    radial-gradient(circle at 30% 80%, rgba(59, 130, 246, 0.15), transparent 25%),
    #0f172a;
  color: #e2e8f0;
  padding: 24px;
}

.auth-card {
  width: 100%;
  max-width: 560px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 20px 70px rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(8px);
}

.auth-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #f8fafc;
}

.auth-header p {
  margin: 6px 0 0;
  color: #cbd5e1;
}

.role-tabs {
  margin-top: 16px;
}

.footer-actions {
  display: flex;
  justify-content: center;
  gap: 8px;
  margin-top: 12px;
  color: #cbd5e1;
}

.footer-actions a {
  color: #a5b4fc;
}
</style>

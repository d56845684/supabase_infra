<template>
  <div class="login-layout">
    <div class="login-card">
      <div class="login-header">
        <h1>{{ $t('auth.loginTitle') }}</h1>
        <p>{{ $t('auth.loginSubtitle') }}</p>
      </div>
      <el-form class="login-form" @submit.prevent="onSubmit">
        <el-form-item :label="$t('auth.email')">
          <el-input v-model="email" autocomplete="username" />
        </el-form-item>
        <el-form-item :label="$t('auth.password')">
          <el-input v-model="password" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <div class="login-meta">
          <div class="role-hint">
            <div>{{ $t('auth.roleHint') }}</div>
            <ul>
              <li>{{ $t('auth.roles.admin') }}</li>
              <li>{{ $t('auth.roles.teacher') }}</li>
              <li>{{ $t('auth.roles.student') }}</li>
            </ul>
          </div>
          <el-button type="primary" :loading="loading" native-type="submit">{{ $t('auth.signIn') }}</el-button>
        </div>
        <el-alert v-if="error" type="error" :title="error" show-icon />
      </el-form>
      <div class="footer-actions">
        <span>{{ $t('auth.noAccount') }}</span>
        <router-link to="/register">{{ $t('auth.createAccount') }}</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAuthStore } from '@/stores/auth';

const email = ref('');
const password = ref('');
const loading = ref(false);
const error = ref('');

const router = useRouter();
const route = useRoute();
const auth = useAuthStore();

const onSubmit = async () => {
  error.value = '';
  loading.value = true;
  try {
    await auth.loginWithEmail(email.value, password.value);
    const redirect = (route.query.redirect as string) || auth.defaultRoute;
    router.push(redirect);
  } catch (err) {
    if (err instanceof Error) {
      error.value = err.message;
    } else {
      error.value = '登入失敗，請稍後再試';
    }
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-layout {
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

.login-card {
  width: 100%;
  max-width: 480px;
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 20px 70px rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(8px);
}

.login-header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 700;
  color: #f8fafc;
}

.login-header p {
  margin: 6px 0 0;
  color: #cbd5e1;
}

.login-form {
  margin-top: 20px;
}

.login-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 8px 0 12px;
}

.role-hint {
  color: #cbd5e1;
  font-size: 13px;
}

.role-hint ul {
  padding-left: 18px;
  margin: 4px 0 0;
}

.role-hint li {
  line-height: 1.5;
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

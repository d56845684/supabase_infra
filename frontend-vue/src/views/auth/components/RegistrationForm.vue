<template>
  <el-form class="registration-form" label-position="top" @submit.prevent="submitForm">
    <el-form-item :label="$t('auth.fullName')">
      <el-input v-model="form.fullName" autocomplete="name" />
    </el-form-item>
    <el-form-item :label="$t('auth.email')">
      <el-input v-model="form.email" type="email" autocomplete="email" />
    </el-form-item>
    <el-form-item :label="$t('auth.password')">
      <el-input v-model="form.password" type="password" show-password autocomplete="new-password" />
    </el-form-item>
    <el-form-item :label="$t('auth.confirmPassword')">
      <el-input
        v-model="form.confirmPassword"
        type="password"
        show-password
        autocomplete="new-password"
      />
    </el-form-item>
    <el-form-item :label="$t('auth.phone')" :required="false">
      <el-input v-model="form.phone" type="tel" autocomplete="tel" />
    </el-form-item>
    <div class="form-hint">
      <p v-if="emailVerificationEnabled">{{ $t('auth.emailVerificationHint') }}</p>
      <p v-else>{{ $t('auth.emailVerificationDisabled') }}</p>
    </div>
    <div class="form-actions">
      <el-button type="primary" :loading="loading" native-type="submit">{{ $t('auth.register') }}</el-button>
    </div>
    <el-alert v-if="error" type="error" :title="error" show-icon />
    <el-alert v-if="success" type="success" :title="success" show-icon class="mt-2" />
  </el-form>
</template>

<script setup lang="ts">
import { reactive } from 'vue';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import type { UserRole } from '@/types/schema';

const props = defineProps<{
  role: UserRole;
  loading: boolean;
  error: string;
  success: string;
  emailVerificationEnabled: boolean;
}>();

const emit = defineEmits<{
  (event: 'submit', payload: {
    fullName: string;
    email: string;
    password: string;
    phone?: string;
    role: UserRole;
  }): void;
}>();

const { t } = useI18n();

const form = reactive({
  fullName: '',
  email: '',
  password: '',
  confirmPassword: '',
  phone: ''
});

const submitForm = () => {
  if (form.password !== form.confirmPassword) {
    ElMessage.error(t('auth.passwordMismatch'));
    return;
  }

  emit('submit', {
    fullName: form.fullName,
    email: form.email,
    password: form.password,
    phone: form.phone,
    role: props.role
  });
};
</script>

<style scoped>
.registration-form {
  margin-top: 12px;
}

.form-hint {
  color: #cbd5e1;
  font-size: 13px;
  margin: 4px 0 12px;
}

.form-actions {
  margin: 8px 0 12px;
}

.mt-2 {
  margin-top: 8px;
}
</style>

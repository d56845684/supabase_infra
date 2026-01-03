<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('nav.backendAccounts') }}</h2>
      <el-tag type="info">{{ users.length }} users</el-tag>
    </div>
    <el-table :data="users" stripe>
      <el-table-column prop="fullName" :label="$t('tables.teacher')" />
      <el-table-column prop="email" :label="$t('tables.email')" />
      <el-table-column prop="role" :label="$t('tables.role')" />
      <el-table-column prop="status" :label="$t('tables.status')">
        <template #default="scope">
          <el-tag type="success">Active</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('tables.operations')">
        <template #default>
          <el-button size="small">Reset Password</el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { useDataStore } from '@/stores/dataStore';
import { storeToRefs } from 'pinia';

const dataStore = useDataStore();
const { users } = storeToRefs(dataStore);
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>

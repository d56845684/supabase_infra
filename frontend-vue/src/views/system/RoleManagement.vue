<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('nav.roles') }}</h2>
      <el-alert type="info" :closable="false" show-icon>
        <template #title>根據 user_role 枚舉模擬權限指派</template>
      </el-alert>
    </div>
    <el-table :data="roleRows" stripe>
      <el-table-column prop="role" :label="$t('tables.role')" />
      <el-table-column prop="permissions" label="Permissions">
        <template #default="scope">
          <el-tag v-for="perm in scope.row.permissions" :key="perm" class="mr-1">{{ perm }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
const roleRows = [
  { role: 'admin', permissions: ['manage_users', 'manage_payroll', 'view_all'] },
  { role: 'teacher', permissions: ['view_own_bookings', 'update_notes'] },
  { role: 'student', permissions: ['create_booking', 'view_own_bookings'] }
];
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>

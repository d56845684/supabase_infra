<template>
  <div class="page">
    <h2>{{ $t('nav.teacherAccounts') }}</h2>
    <el-table :data="teacherUsers" stripe>
      <el-table-column prop="fullName" :label="$t('tables.teacher')" />
      <el-table-column prop="email" :label="$t('tables.email')" />
      <el-table-column :label="$t('tables.status')">
        <template #default>
          <el-tag type="success">Active</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useDataStore } from '@/stores/dataStore';

const dataStore = useDataStore();
const teacherUsers = computed(() => dataStore.users.filter((u) => u.role === 'teacher'));
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>

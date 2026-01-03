<template>
  <div class="page">
    <h2>{{ $t('nav.teacherLeave') }}</h2>
    <el-table :data="leaveRows" stripe>
      <el-table-column prop="teacher" :label="$t('tables.teacher')" />
      <el-table-column prop="date" :label="$t('tables.date')" />
      <el-table-column prop="reason" :label="$t('tables.reason')" />
      <el-table-column prop="status" :label="$t('tables.status')">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'approved' ? 'success' : 'warning'">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('tables.operations')">
        <template #default="scope">
          <el-button
            size="small"
            type="primary"
            :disabled="scope.row.status === 'approved'"
            @click="approve(scope.row.id)"
          >
            {{ $t('actions.approve') }}
          </el-button>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useDataStore } from '@/stores/dataStore';

const dataStore = useDataStore();

const leaveRows = computed(() =>
  dataStore.leaveRequests.map((req) => ({
    ...req,
    teacher: dataStore.users.find((u) => u.id === req.teacherId)?.fullName ?? req.teacherId
  }))
);

const approve = (id: string) => dataStore.approveLeave(id);
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>

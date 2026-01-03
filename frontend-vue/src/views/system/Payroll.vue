<template>
  <div class="page">
    <h2>{{ $t('nav.payroll') }}</h2>
    <el-table :data="payrollRows" stripe>
      <el-table-column prop="teacher" :label="$t('tables.teacher')" />
      <el-table-column prop="period" :label="$t('tables.period')" />
      <el-table-column prop="totalLessons" :label="$t('tables.lessons')" />
      <el-table-column prop="finalAmount" :label="$t('tables.amount')">
        <template #default="scope">${{ scope.row.finalAmount.toFixed(2) }}</template>
      </el-table-column>
      <el-table-column prop="status" :label="$t('tables.status')">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'pending' ? 'warning' : 'success'">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import dayjs from 'dayjs';
import { computed } from 'vue';
import { useDataStore } from '@/stores/dataStore';

const dataStore = useDataStore();
const payrollRows = computed(() =>
  dataStore.payrolls.map((row) => {
    const teacher = dataStore.users.find((u) => u.id === row.teacherId);
    return {
      ...row,
      teacher: teacher?.fullName ?? row.teacherId,
      period: `${dayjs(row.periodStart).format('MM/DD')} - ${dayjs(row.periodEnd).format('MM/DD')}`
    };
  })
);
</script>

<style scoped>
.page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
</style>

<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('nav.studentBookings') }}</h2>
      <el-button size="small" type="primary" @click="createBooking">{{ $t('actions.addBooking') }}</el-button>
    </div>
    <el-table :data="rows" stripe>
      <el-table-column prop="student" :label="$t('tables.student')" />
      <el-table-column prop="teacher" :label="$t('tables.teacher')" />
      <el-table-column prop="schedule" :label="$t('tables.schedule')" />
      <el-table-column prop="status" :label="$t('tables.status')">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'completed' ? 'success' : 'info'">{{ scope.row.status }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import dayjs from 'dayjs';
import { useDataStore } from '@/stores/dataStore';
import { nanoid } from 'nanoid';

const dataStore = useDataStore();

const rows = computed(() =>
  dataStore.bookingView.map((b) => ({
    ...b,
    student: b.student?.fullName ?? b.studentId,
    teacher: b.teacher?.fullName ?? b.teacherId,
    schedule: `${dayjs(b.scheduledStart).format('MM/DD HH:mm')} - ${dayjs(b.scheduledEnd).format('HH:mm')}`
  }))
);

const createBooking = () => {
  dataStore.addBooking({
    id: nanoid(),
    studentId: 'student-1',
    teacherId: 'teacher-1',
    scheduledStart: dayjs().add(2, 'day').hour(11).minute(0).toISOString(),
    scheduledEnd: dayjs().add(2, 'day').hour(12).minute(0).toISOString(),
    status: 'scheduled'
  });
};
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

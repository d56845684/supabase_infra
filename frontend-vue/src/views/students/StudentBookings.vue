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
import { ElMessage } from 'element-plus';

const dataStore = useDataStore();

const rows = computed(() =>
  dataStore.bookingView.map((b) => ({
    ...b,
    student: b.student?.full_name ?? b.student_id,
    teacher: b.teacher?.full_name ?? b.teacher_id,
    schedule: `${dayjs(b.scheduled_start).format('MM/DD HH:mm')} - ${dayjs(b.scheduled_end).format('HH:mm')}`
  }))
);

const createBooking = async () => {
  const studentId = dataStore.students[0]?.id;
  const teacherId = dataStore.teachers[0]?.id;
  if (!studentId || !teacherId) {
    ElMessage.error('缺少可用的學生或老師資料');
    return;
  }

  try {
    await dataStore.addBooking({
      id: nanoid(),
      student_id: studentId,
      teacher_id: teacherId,
      scheduled_start: dayjs().add(2, 'day').hour(11).minute(0).toISOString(),
      scheduled_end: dayjs().add(2, 'day').hour(12).minute(0).toISOString(),
      status: 'scheduled'
    });
    ElMessage.success('已建立新預約');
  } catch (error) {
    console.error(error);
    ElMessage.error('建立預約時發生錯誤');
  }
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

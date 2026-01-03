<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('nav.bookingOverview') }}</h2>
      <el-select v-model="selectedTeacher" placeholder="Select" size="small">
        <el-option v-for="teacher in teacherUsers" :key="teacher.id" :label="teacher.fullName" :value="teacher.id" />
      </el-select>
    </div>
    <div class="chart" ref="chartRef"></div>
    <el-table :data="bookingRows" stripe>
      <el-table-column prop="schedule" :label="$t('tables.schedule')" />
      <el-table-column prop="student" :label="$t('tables.student')" />
      <el-table-column prop="status" :label="$t('tables.status')" />
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue';
import * as echarts from 'echarts';
import dayjs from 'dayjs';
import { useDataStore } from '@/stores/dataStore';

const dataStore = useDataStore();
const chartRef = ref<HTMLDivElement>();
const selectedTeacher = ref<string>('');

const teacherUsers = computed(() => dataStore.users.filter((u) => u.role === 'teacher'));

watch(
  teacherUsers,
  (list) => {
    if (!selectedTeacher.value && list.length > 0) {
      selectedTeacher.value = list[0].id;
    }
  },
  { immediate: true }
);

const bookingRows = computed(() =>
  dataStore.bookingView
    .filter((b) => b.teacherId === selectedTeacher.value)
    .map((b) => ({
      ...b,
      schedule: `${dayjs(b.scheduledStart).format('MM/DD HH:mm')} - ${dayjs(b.scheduledEnd).format('HH:mm')}`,
      student: b.student?.fullName ?? b.studentId
    }))
);

const renderChart = () => {
  if (!chartRef.value) return;
  const chart = echarts.init(chartRef.value);
  const grouped = bookingRows.value.reduce<Record<string, number>>((acc, cur) => {
    const day = dayjs(cur.scheduledStart).format('MM/DD');
    acc[day] = (acc[day] || 0) + 1;
    return acc;
  }, {});
  const days = Object.keys(grouped);
  const counts = days.map((day) => grouped[day]);
  chart.setOption({
    tooltip: {},
    xAxis: { type: 'category', data: days },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: counts, name: 'Bookings' }]
  });
};

onMounted(() => {
  nextTick(renderChart);
});

watch(bookingRows, () => nextTick(renderChart));
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

.chart {
  width: 100%;
  height: 240px;
}
</style>

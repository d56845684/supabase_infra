<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('nav.teacherProfiles') }}</h2>
      <el-button size="small" type="primary">新增老師</el-button>
    </div>
    <el-table :data="rows" stripe>
      <el-table-column prop="profile.fullName" :label="$t('tables.teacher')" />
      <el-table-column prop="profile.email" :label="$t('tables.email')" />
      <el-table-column prop="specialties" label="Specialties">
        <template #default="scope">
          <el-tag v-for="skill in scope.row.specialties" :key="skill" class="mr-1">{{ skill }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="languages" label="Languages">
        <template #default="scope">
          <el-tag v-for="lang in scope.row.languages" :key="lang" class="mr-1">{{ lang }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="status" :label="$t('tables.status')">
        <template #default="scope">
          <el-select v-model="scope.row.status" size="small" @change="(v) => changeStatus(scope.row.id, v)">
            <el-option value="pending" label="pending" />
            <el-option value="active" label="active" />
            <el-option value="suspended" label="suspended" />
          </el-select>
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';
import { useDataStore } from '@/stores/dataStore';
import { ElMessage } from 'element-plus';

const dataStore = useDataStore();
const { teacherProfiles: rows } = storeToRefs(dataStore);

const changeStatus = async (id: string, status: string) => {
  try {
    await dataStore.updateTeacherStatus(id, status as any);
    ElMessage.success('老師狀態已更新');
  } catch (error) {
    console.error(error);
    ElMessage.error('更新老師狀態時發生錯誤');
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
  gap: 8px;
}
</style>

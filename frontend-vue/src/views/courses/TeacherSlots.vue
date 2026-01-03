<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('nav.teacherSlots') }}</h2>
      <el-button type="primary" size="small" @click="openDialog">{{ $t('slotForm.add') }}</el-button>
    </div>

    <el-form inline class="filter-row">
      <el-form-item :label="$t('slotForm.teacher')">
        <el-select v-model="selectedTeacherId" :disabled="!isAdmin" filterable>
          <el-option v-for="teacher in teacherOptions" :key="teacher.value" :label="teacher.label" :value="teacher.value" />
        </el-select>
      </el-form-item>
    </el-form>

    <el-table :data="selectedSlots" stripe>
      <el-table-column :label="$t('slotForm.teacher')" prop="teacher" />
      <el-table-column :label="$t('slotForm.start')" prop="start" />
      <el-table-column :label="$t('slotForm.end')" prop="end" />
      <el-table-column :label="$t('slotForm.visibility')">
        <template #default="scope">
          <el-tag size="small" type="info" v-if="scope.row.visible_to_all">
            {{ $t('slotForm.visibilityAll') }}
          </el-tag>
          <div v-else class="student-list">
            <div class="chip">{{ $t('slotForm.visibilitySpecific') }}</div>
            <div class="chips">
              <span v-for="student in scope.row.allowedStudents" :key="student" class="chip">{{ student }}</span>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="$t('slotForm.isOpen')">
        <template #default="scope">
          <el-tag :type="scope.row.is_open ? 'success' : 'warning'">
            {{ scope.row.is_open ? $t('slotForm.openLabel') : $t('slotForm.closedLabel') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('slotForm.notes')" prop="notes" />
    </el-table>

    <el-dialog v-model="dialogVisible" :title="$t('slotForm.title')" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="140px">
        <el-form-item :label="$t('slotForm.teacher')" prop="teacher_id">
          <el-select v-model="form.teacher_id" :disabled="!isAdmin" filterable>
            <el-option v-for="teacher in teacherOptions" :key="teacher.value" :label="teacher.label" :value="teacher.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('slotForm.start')" prop="slot_start">
          <el-date-picker
            v-model="form.slot_start"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            :placeholder="$t('slotForm.start')"
          />
        </el-form-item>
        <el-form-item :label="$t('slotForm.end')" prop="slot_end">
          <el-date-picker
            v-model="form.slot_end"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            :placeholder="$t('slotForm.end')"
          />
        </el-form-item>
        <el-form-item :label="$t('slotForm.isOpen')">
          <el-switch v-model="form.is_open" />
        </el-form-item>
        <el-form-item :label="$t('slotForm.visibility')">
          <el-radio-group v-model="visibilityMode">
            <el-radio label="all">{{ $t('slotForm.visibilityAll') }}</el-radio>
            <el-radio label="specific">{{ $t('slotForm.visibilitySpecific') }}</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="visibilityMode === 'specific'" :label="$t('slotForm.students')" prop="visible_student_ids">
          <el-select
            v-model="form.visible_student_ids"
            multiple
            filterable
            :placeholder="$t('slotForm.students')"
          >
            <el-option v-for="student in studentOptions" :key="student.value" :label="student.label" :value="student.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('slotForm.notes')">
          <el-input v-model="form.notes" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeDialog">{{ $t('slotForm.cancel') }}</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">{{ $t('slotForm.submit') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import { useI18n } from 'vue-i18n';
import { ElMessage } from 'element-plus';
import { useAuthStore } from '@/stores/auth';
import { useDataStore } from '@/stores/dataStore';
import type { FormInstance, FormRules } from 'element-plus';
import type { TeacherAvailableSlot } from '@/types/schema';

const { t } = useI18n();
const authStore = useAuthStore();
const dataStore = useDataStore();

const dialogVisible = ref(false);
const saving = ref(false);
const formRef = ref<FormInstance>();
const visibilityMode = ref<'all' | 'specific'>('all');

const form = reactive<Partial<TeacherAvailableSlot>>({
  teacher_id: '',
  slot_start: '',
  slot_end: '',
  is_open: true,
  visible_to_all: true,
  visible_student_ids: [],
  notes: ''
});

const isAdmin = computed(() => authStore.currentUser?.role === 'admin');
const teacherOptions = computed(() =>
  dataStore.teachers.map((teacher) => ({
    value: teacher.id,
    label: teacherLabel(teacher.id)
  }))
);

const studentOptions = computed(() =>
  dataStore.students.map((student) => ({
    value: student.id,
    label: studentLabel(student.id)
  }))
);

const selectedTeacherId = ref('');

const teacherLabel = (id: string) => {
  const user = dataStore.users.find((u) => u.id === id);
  if (user?.full_name && user.email) return `${user.full_name} (${user.email})`;
  if (user?.full_name) return user.full_name;
  if (user?.email) return user.email;
  return t('labels.unknownUser');
};

const studentLabel = (id: string) => {
  const user = dataStore.users.find((u) => u.id === id);
  if (user?.full_name && user.email) return `${user.full_name} (${user.email})`;
  if (user?.full_name) return user.full_name;
  if (user?.email) return user.email;
  return t('labels.unknownUser');
};

const selectedSlots = computed(() =>
  dataStore.teacherSlots
    .filter((slot) => slot.teacher_id === selectedTeacherId.value)
    .map((slot) => ({
      ...slot,
      teacher: teacherLabel(slot.teacher_id),
      start: dayjs(slot.slot_start).format('YYYY/MM/DD HH:mm'),
      end: dayjs(slot.slot_end).format('YYYY/MM/DD HH:mm'),
      allowedStudents: (slot.visible_student_ids ?? []).map(studentLabel)
    }))
);

watch(
  () => authStore.currentUser,
  () => {
    const defaultTeacher = isAdmin.value ? teacherOptions.value[0]?.value : authStore.currentUser?.id;
    selectedTeacherId.value = defaultTeacher ?? '';
    form.teacher_id = defaultTeacher ?? '';
  },
  { immediate: true }
);

watch(
  () => teacherOptions.value,
  (options) => {
    if (!selectedTeacherId.value && options.length) {
      const defaultTeacher = isAdmin.value ? options[0].value : authStore.currentUser?.id;
      selectedTeacherId.value = defaultTeacher ?? '';
      form.teacher_id = defaultTeacher ?? '';
    }
  },
  { deep: true }
);

watch(
  () => visibilityMode.value,
  (mode) => {
    form.visible_to_all = mode === 'all';
    if (mode === 'all') form.visible_student_ids = [];
  }
);

const rules: FormRules = {
  teacher_id: [{ required: true, message: t('slotForm.validation.teacher'), trigger: 'change' }],
  slot_start: [
    { required: true, message: t('slotForm.validation.start'), trigger: 'change' },
    {
      validator: (_, value, callback) => {
        if (value && form.slot_end && dayjs(value).isAfter(dayjs(form.slot_end))) {
          callback(new Error(t('slotForm.validation.endAfterStart')));
        } else {
          callback();
        }
      },
      trigger: 'change'
    }
  ],
  slot_end: [
    { required: true, message: t('slotForm.validation.end'), trigger: 'change' },
    {
      validator: (_, value, callback) => {
        if (value && form.slot_start && dayjs(value).isBefore(dayjs(form.slot_start))) {
          callback(new Error(t('slotForm.validation.endAfterStart')));
        } else {
          callback();
        }
      },
      trigger: 'change'
    }
  ],
  visible_student_ids: [
    {
      validator: (_, value, callback) => {
        if (visibilityMode.value === 'specific' && (!value || (value as string[]).length === 0)) {
          callback(new Error(t('slotForm.validation.students')));
          return;
        }
        callback();
      },
      trigger: 'change'
    }
  ]
};

const resetForm = () => {
  form.teacher_id = selectedTeacherId.value;
  form.slot_start = '';
  form.slot_end = '';
  form.is_open = true;
  form.visible_to_all = true;
  form.visible_student_ids = [];
  form.notes = '';
  visibilityMode.value = 'all';
};

const openDialog = () => {
  resetForm();
  dialogVisible.value = true;
};

const closeDialog = () => {
  dialogVisible.value = false;
};

const hasOverlap = (start: string, end: string) => {
  const startAt = dayjs(start);
  const endAt = dayjs(end);
  return dataStore.teacherSlots.some((slot) => {
    if (slot.teacher_id !== form.teacher_id) return false;
    const existingStart = dayjs(slot.slot_start);
    const existingEnd = dayjs(slot.slot_end);
    return startAt.isBefore(existingEnd) && endAt.isAfter(existingStart);
  });
};

const submitForm = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
  } catch (error) {
    return;
  }

  if (!form.slot_start || !form.slot_end || !form.teacher_id) return;
  if (hasOverlap(form.slot_start, form.slot_end)) {
    ElMessage.error(t('slotForm.overlapError'));
    return;
  }

  saving.value = true;
  try {
    await dataStore.addTeacherSlot({
      teacher_id: form.teacher_id,
      slot_start: form.slot_start,
      slot_end: form.slot_end,
      is_open: form.is_open ?? true,
      visible_to_all: visibilityMode.value === 'all',
      visible_student_ids: visibilityMode.value === 'specific' ? form.visible_student_ids : [],
      notes: form.notes
    });
    dialogVisible.value = false;
    ElMessage.success(t('slotForm.success'));
  } catch (error) {
    console.error(error);
    ElMessage.error(t('slotForm.failure'));
  } finally {
    saving.value = false;
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

.filter-row {
  margin-bottom: 8px;
}

.student-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.chip {
  background: var(--el-color-info-light-9);
  color: var(--el-color-info);
  border-radius: 4px;
  padding: 2px 6px;
  font-size: 12px;
}
</style>

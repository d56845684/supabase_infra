<template>
  <div class="page">
    <div class="page-header">
      <h2>{{ $t('nav.studentBookings') }}</h2>
      <el-button size="small" type="primary" @click="openDialog">{{ $t('actions.addBooking') }}</el-button>
    </div>
    <el-table :data="rows" stripe>
      <el-table-column prop="student" :label="$t('tables.student')" />
      <el-table-column prop="teacher" :label="$t('tables.teacher')" />
      <el-table-column prop="schedule" :label="$t('tables.schedule')" />
      <el-table-column prop="status" :label="$t('tables.status')">
        <template #default="scope">
          <el-tag :type="scope.row.status === 'completed' ? 'success' : 'info'">
            {{ statusLabel(scope.row.status) }}
          </el-tag>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="$t('bookingForm.title')" width="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="120px">
        <el-form-item :label="$t('bookingForm.student')" prop="student_id">
          <el-select v-model="form.student_id" filterable :placeholder="$t('bookingForm.studentPlaceholder')">
            <el-option v-for="student in studentOptions" :key="student.value" :label="student.label" :value="student.value" />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('bookingForm.slot')" prop="slot_id">
          <el-select v-model="form.slot_id" filterable :placeholder="$t('bookingForm.slotPlaceholder')">
            <el-option
              v-for="slot in slotOptions"
              :key="slot.value"
              :label="slot.label"
              :value="slot.value"
              :disabled="slot.disabled"
            />
          </el-select>
        </el-form-item>
        <el-form-item :label="$t('bookingForm.teacher')" prop="teacher_id">
          <el-input v-model="teacherLabel" disabled />
        </el-form-item>
        <el-form-item :label="$t('bookingForm.start')" prop="scheduled_start">
          <el-date-picker
            v-model="form.scheduled_start"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            :placeholder="$t('bookingForm.startPlaceholder')"
            disabled
          />
        </el-form-item>
        <el-form-item :label="$t('bookingForm.end')" prop="scheduled_end">
          <el-date-picker
            v-model="form.scheduled_end"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            :placeholder="$t('bookingForm.endPlaceholder')"
            disabled
          />
        </el-form-item>
        <el-form-item :label="$t('bookingForm.status')" prop="status">
          <el-select v-model="form.status">
            <el-option
              v-for="status in statusOptions"
              :key="status"
              :label="statusLabel(status)"
              :value="status"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="closeDialog">{{ $t('bookingForm.cancel') }}</el-button>
          <el-button type="primary" :loading="saving" @click="submitForm">{{ $t('bookingForm.submit') }}</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue';
import dayjs from 'dayjs';
import { useI18n } from 'vue-i18n';
import { useDataStore } from '@/stores/dataStore';
import { ElMessage } from 'element-plus';
import type { Booking } from '@/types/schema';
import type { FormInstance, FormRules } from 'element-plus';

const dataStore = useDataStore();
const { t } = useI18n();

const statusOptions: Booking['status'][] = ['scheduled', 'completed', 'cancelled', 'no_show'];
const dialogVisible = ref(false);
const saving = ref(false);
const formRef = ref<FormInstance>();
const form = reactive<{
  student_id: string;
  slot_id: string;
  teacher_id: string;
  scheduled_start: string;
  scheduled_end: string;
  status: Booking['status'];
}>({
  student_id: '',
  slot_id: '',
  teacher_id: '',
  scheduled_start: '',
  scheduled_end: '',
  status: 'scheduled'
});

const userLabel = (id: string) => {
  const user = dataStore.users.find((u) => u.id === id);
  if (user?.full_name && user?.email) return `${user.full_name} (${user.email})`;
  if (user?.full_name) return user.full_name;
  if (user?.email) return user.email;
  return t('labels.unknownUser');
};

const rows = computed(() =>
  dataStore.bookingView.map((b) => ({
    ...b,
    student: b.student_name ?? userLabel(b.student_id),
    teacher: b.teacher_name ?? userLabel(b.teacher_id),
    schedule: `${dayjs(b.scheduled_start).format('MM/DD HH:mm')} - ${dayjs(b.scheduled_end).format('HH:mm')}`
  }))
);

const studentOptions = computed(() =>
  dataStore.students.map((student) => ({
    value: student.id,
    label: userLabel(student.id)
  }))
);

const openSlots = computed(() => dataStore.teacherSlots.filter((slot) => slot.is_open));

const slotOptions = computed(() =>
  openSlots.value.map((slot) => ({
    value: slot.id,
    label: `${userLabel(slot.teacher_id)} | ${dayjs(slot.slot_start).format('MM/DD HH:mm')} - ${dayjs(
      slot.slot_end
    ).format('HH:mm')}`,
    disabled: !slot.is_open
  }))
);

const teacherLabel = computed(() => userLabel(form.teacher_id));

const rules: FormRules = {
  student_id: [{ required: true, message: t('bookingForm.validation.student'), trigger: 'change' }],
  slot_id: [{ required: true, message: t('bookingForm.validation.slot'), trigger: 'change' }],
  teacher_id: [{ required: true, message: t('bookingForm.validation.teacher'), trigger: 'change' }],
  scheduled_start: [{ required: true, message: t('bookingForm.validation.start'), trigger: 'change' }],
  scheduled_end: [{ required: true, message: t('bookingForm.validation.end'), trigger: 'change' }]
};

const generateUuid = () =>
  typeof crypto !== 'undefined' && 'randomUUID' in crypto
    ? crypto.randomUUID()
    : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
        const r = (Math.random() * 16) | 0;
        const v = c === 'x' ? r : (r & 0x3) | 0x8;
        return v.toString(16);
      });

const resetForm = () => {
  form.student_id = studentOptions.value[0]?.value ?? '';
  form.slot_id = slotOptions.value[0]?.value ?? '';
  const slot = openSlots.value.find((s) => s.id === form.slot_id);
  form.teacher_id = slot?.teacher_id ?? '';
  form.scheduled_start = slot?.slot_start ?? '';
  form.scheduled_end = slot?.slot_end ?? '';
  form.status = 'scheduled';
};

const openDialog = () => {
  if (!studentOptions.value.length || !slotOptions.value.length) {
    ElMessage.error(t('bookingForm.validation.noProfiles'));
    return;
  }
  resetForm();
  dialogVisible.value = true;
};

const closeDialog = () => {
  dialogVisible.value = false;
};

watch(
  () => form.slot_id,
  (slotId) => {
    const slot = openSlots.value.find((s) => s.id === slotId);
    if (!slot) return;
    form.teacher_id = slot.teacher_id;
    form.scheduled_start = slot.slot_start;
    form.scheduled_end = slot.slot_end;
  }
);

const statusLabel = (status: Booking['status']) => t(`bookingForm.statusLabels.${status}`);

const submitForm = async () => {
  if (!formRef.value) return;
  try {
    await formRef.value.validate();
  } catch (error) {
    return;
  }

  saving.value = true;
  try {
    await dataStore.addBooking({
      id: generateUuid(),
      student_id: form.student_id,
      teacher_id: form.teacher_id,
      slot_id: form.slot_id,
      scheduled_start: dayjs(form.scheduled_start).toISOString(),
      scheduled_end: dayjs(form.scheduled_end).toISOString(),
      status: form.status
    });
    dialogVisible.value = false;
    ElMessage.success(t('bookingForm.success'));
  } catch (error) {
    console.error(error);
    ElMessage.error(t('bookingForm.failure'));
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
</style>

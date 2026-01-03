import { defineStore } from 'pinia';
import type {
  Booking,
  BookingManagement,
  Student,
  Teacher,
  TeacherAvailableSlot,
  TeacherPayroll,
  UserProfile
} from '@/types/schema';
import { supabase } from '@/lib/supabase';

interface State {
  users: UserProfile[];
  teachers: Teacher[];
  students: Student[];
  bookings: BookingManagement[];
  teacherSlots: TeacherAvailableSlot[];
  payrolls: TeacherPayroll[];
  initialized: boolean;
}

export const useDataStore = defineStore('data', {
  state: (): State => ({
    users: [],
    teachers: [],
    students: [],
    bookings: [],
    teacherSlots: [],
    payrolls: [],
    initialized: false
  }),
  getters: {
    teacherProfiles: (state) => state.teachers.map((t) => ({
      ...t,
      profile: state.users.find((u) => u.id === t.id)
    })),
    studentProfiles: (state) => state.students.map((s) => ({
      ...s,
      profile: state.users.find((u) => u.id === s.id)
    })),
    bookingView: (state) => state.bookings
  },
  actions: {
    async ensureInitialized() {
      if (this.initialized) return;
      await this.refreshAll();
      this.initialized = true;
    },
    async refreshAll() {
      await Promise.all([
        this.fetchUsers(),
        this.fetchTeachers(),
        this.fetchStudents(),
        this.fetchBookings(),
        this.fetchTeacherSlots(),
        this.fetchPayrolls()
      ]);
    },
    async fetchUsers() {
      const { data, error } = await supabase.from('user_profiles').select('*');
      if (error) throw error;
      this.users = (data ?? []) as UserProfile[];
    },
    async fetchTeachers() {
      const { data, error } = await supabase.from('teachers').select('*');
      if (error) throw error;
      this.teachers = (data ?? []) as Teacher[];
    },
    async fetchStudents() {
      const { data, error } = await supabase.from('students').select('*');
      if (error) throw error;
      this.students = (data ?? []) as Student[];
    },
    async fetchBookings() {
      const { data, error } = await supabase.from('v_booking_management').select('*');
      if (error) throw error;
      this.bookings = (data ?? []) as BookingManagement[];
    },
    async fetchTeacherSlots() {
      const { data, error } = await supabase
        .from('teacher_available_slots')
        .select('*')
        .order('slot_start', { ascending: true });
      if (error) throw error;
      this.teacherSlots = (data ?? []) as TeacherAvailableSlot[];
    },
    async fetchPayrolls() {
      const { data, error } = await supabase.from('teacher_payroll').select('*');
      if (error) throw error;
      this.payrolls = (data ?? []) as TeacherPayroll[];
    },
    async upsertUser(user: UserProfile) {
      const { error, data } = await supabase
        .from('user_profiles')
        .upsert(user, { onConflict: 'id' })
        .select()
        .single();
      if (error) throw error;
      const next = (data as UserProfile) ?? user;
      const idx = this.users.findIndex((u) => u.id === next.id);
      if (idx >= 0) this.users[idx] = next;
      else this.users.push(next);
    },
    async updateTeacherStatus(id: string, status: Teacher['teacher_status']) {
      const { data, error } = await supabase
        .from('teachers')
        .update({ teacher_status: status })
        .eq('id', id)
        .select()
        .single();
      if (error) throw error;
      const idx = this.teachers.findIndex((t) => t.id === id);
      if (idx >= 0 && data) this.teachers[idx] = data as Teacher;
    },
    async addBooking(booking: Booking) {
      const { data, error } = await supabase.from('bookings').insert(booking).select().single();
      if (error) throw error;
      const createdId = ((data as Booking | null)?.id ?? booking.id) as string;

      const { data: viewRow, error: viewError } = await supabase
        .from('v_booking_management')
        .select('*')
        .eq('id', createdId)
        .single();
      if (viewError) throw viewError;

      const next = (viewRow as BookingManagement | null) ?? (booking as BookingManagement);
      this.bookings.push(next);
    }
  }
});

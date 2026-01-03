import { defineStore } from 'pinia';
import dayjs from 'dayjs';
import type {
  Booking,
  Student,
  Teacher,
  TeacherLeaveRequest,
  TeacherPayroll,
  UserProfile
} from '@/types/schema';

interface State {
  users: UserProfile[];
  teachers: Teacher[];
  students: Student[];
  bookings: Booking[];
  payrolls: TeacherPayroll[];
  leaveRequests: TeacherLeaveRequest[];
}

export const useDataStore = defineStore('data', {
  state: (): State => ({
    users: [
      { id: 'admin-1', role: 'admin', fullName: 'Admin User', email: 'admin@example.com' },
      { id: 'teacher-1', role: 'teacher', fullName: 'Teacher Jane', email: 'teacher@example.com' },
      { id: 'teacher-2', role: 'teacher', fullName: 'Teacher Mike', email: 'mike@example.com' },
      { id: 'student-1', role: 'student', fullName: 'Student Ray', email: 'student@example.com' },
      { id: 'student-2', role: 'student', fullName: 'Student Wendy', email: 'wendy@example.com' }
    ],
    teachers: [
      {
        id: 'teacher-1',
        profileId: 'teacher-1',
        status: 'active',
        specialties: ['IELTS', 'Business English'],
        languages: ['EN', 'ZH'],
        hourlyRate: 35,
        bankName: 'Taiwan Bank',
        bankAccount: '123-456-789'
      },
      {
        id: 'teacher-2',
        profileId: 'teacher-2',
        status: 'pending',
        specialties: ['Conversation'],
        languages: ['EN'],
        hourlyRate: 28
      }
    ],
    students: [
      { id: 'student-1', profileId: 'student-1', status: 'active' },
      { id: 'student-2', profileId: 'student-2', status: 'trial' }
    ],
    bookings: [
      {
        id: 'booking-1',
        studentId: 'student-1',
        teacherId: 'teacher-1',
        scheduledStart: dayjs().add(1, 'day').hour(9).minute(0).toISOString(),
        scheduledEnd: dayjs().add(1, 'day').hour(10).minute(0).toISOString(),
        status: 'scheduled'
      },
      {
        id: 'booking-2',
        studentId: 'student-2',
        teacherId: 'teacher-2',
        scheduledStart: dayjs().subtract(1, 'day').hour(15).minute(0).toISOString(),
        scheduledEnd: dayjs().subtract(1, 'day').hour(16).minute(0).toISOString(),
        status: 'completed'
      }
    ],
    payrolls: [
      {
        id: 'payroll-1',
        teacherId: 'teacher-1',
        periodStart: dayjs().startOf('month').toISOString(),
        periodEnd: dayjs().endOf('month').toISOString(),
        totalLessons: 18,
        totalHours: 18,
        baseAmount: 630,
        bonusAmount: 50,
        deductionAmount: 20,
        finalAmount: 660,
        status: 'pending'
      }
    ],
    leaveRequests: [
      {
        id: 'leave-1',
        teacherId: 'teacher-1',
        date: dayjs().add(2, 'day').format('YYYY-MM-DD'),
        reason: 'Medical appointment',
        status: 'pending'
      },
      {
        id: 'leave-2',
        teacherId: 'teacher-2',
        date: dayjs().add(3, 'day').format('YYYY-MM-DD'),
        reason: 'Family trip',
        status: 'approved'
      }
    ]
  }),
  getters: {
    teacherProfiles: (state) => state.teachers.map((t) => ({
      ...t,
      profile: state.users.find((u) => u.id === t.profileId)
    })),
    studentProfiles: (state) => state.students.map((s) => ({
      ...s,
      profile: state.users.find((u) => u.id === s.profileId)
    })),
    bookingView: (state) => state.bookings.map((b) => ({
      ...b,
      student: state.users.find((u) => u.id === b.studentId),
      teacher: state.users.find((u) => u.id === b.teacherId)
    }))
  },
  actions: {
    upsertUser(user: UserProfile) {
      const idx = this.users.findIndex((u) => u.id === user.id);
      if (idx >= 0) this.users[idx] = user;
      else this.users.push(user);
    },
    updateTeacherStatus(id: string, status: Teacher['status']) {
      const teacher = this.teachers.find((t) => t.id === id);
      if (teacher) teacher.status = status;
    },
    approveLeave(id: string) {
      const request = this.leaveRequests.find((r) => r.id === id);
      if (request) request.status = 'approved';
    },
    addBooking(booking: Booking) {
      this.bookings.push(booking);
    }
  }
});

export type UserRole = 'admin' | 'teacher' | 'student';

export interface UserProfile {
  id: string;
  role: UserRole;
  fullName: string;
  email: string;
  phone?: string;
}

export interface Teacher {
  id: string;
  profileId: string;
  status: 'pending' | 'active' | 'suspended' | 'inactive';
  specialties: string[];
  languages: string[];
  hourlyRate: number;
  bankName?: string;
  bankAccount?: string;
}

export interface TeacherPayroll {
  id: string;
  teacherId: string;
  periodStart: string;
  periodEnd: string;
  totalLessons: number;
  totalHours: number;
  baseAmount: number;
  bonusAmount: number;
  deductionAmount: number;
  finalAmount: number;
  status: 'pending' | 'completed' | 'failed' | 'refunded';
}

export interface TeacherLeaveRequest {
  id: string;
  teacherId: string;
  date: string;
  reason: string;
  status: 'pending' | 'approved' | 'rejected';
}

export interface Student {
  id: string;
  profileId: string;
  status: 'trial' | 'active' | 'suspended' | 'inactive';
}

export interface Booking {
  id: string;
  studentId: string;
  teacherId: string;
  scheduledStart: string;
  scheduledEnd: string;
  status: 'scheduled' | 'completed' | 'cancelled' | 'no_show';
  contractId?: string;
  zoomAccountId?: string;
}

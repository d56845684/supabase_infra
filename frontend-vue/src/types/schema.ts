export type UserRole = 'admin' | 'teacher' | 'student';

export interface UserProfile {
  id: string;
  role: UserRole;
  full_name: string;
  email: string;
  phone?: string;
  avatar_url?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Teacher {
  id: string;
  teacher_status: 'pending' | 'active' | 'suspended' | 'inactive';
  specialties?: string[];
  languages?: string[];
  hourly_rate?: number;
  bank_account?: string;
  bank_name?: string;
  tax_id?: string;
  bio?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TeacherPayroll {
  id: string;
  teacher_id: string;
  period_start: string;
  period_end: string;
  total_lessons: number;
  total_hours: number;
  base_amount: number;
  bonus_amount: number;
  deduction_amount: number;
  final_amount: number;
  payment_status: 'pending' | 'completed' | 'failed' | 'refunded';
  payment_date?: string;
  notes?: string;
  created_by?: string;
  created_at?: string;
}

export interface Student {
  id: string;
  student_status: 'trial' | 'active' | 'suspended' | 'inactive';
  trial_start_date?: string;
  trial_end_date?: string;
  formal_start_date?: string;
  emergency_contact?: string;
  emergency_phone?: string;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface Booking {
  id: string;
  student_id: string;
  teacher_id: string;
  slot_id?: string;
  scheduled_start: string;
  scheduled_end: string;
  status: 'scheduled' | 'completed' | 'cancelled' | 'no_show';
  contract_id?: string;
  zoom_account_id?: string;
  actual_start?: string;
  actual_end?: string;
  zoom_meeting_id?: string;
  zoom_join_url?: string;
  zoom_start_url?: string;
  zoom_password?: string;
  google_calendar_event_id?: string;
  recording_url?: string;
  recording_password?: string;
  recording_duration?: number;
  lesson_notes?: string;
  student_feedback?: string;
  teacher_feedback?: string;
  created_at?: string;
  updated_at?: string;
}

export interface BookingManagement extends Booking {
  student_name?: string;
  student_email?: string;
  teacher_name?: string;
  teacher_email?: string;
  slot_start?: string;
  slot_end?: string;
  slot_is_open?: boolean;
}

export interface TeacherAvailableSlot {
  id: string;
  teacher_id: string;
  slot_start: string;
  slot_end: string;
  is_open: boolean;
  visible_to_all?: boolean;
  visible_student_ids?: string[];
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

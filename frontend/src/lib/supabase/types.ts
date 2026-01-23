// Database types placeholder
// Run `npm run supabase:gen-types` to generate actual types

export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[]

export type Database = {
  public: {
    Tables: {
      user_profiles: {
        Row: {
          id: string
          role: string
          full_name: string
          email: string
          phone: string | null
          avatar_url: string | null
          created_at: string
          updated_at: string
          [key: string]: unknown
        }
        Insert: {
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
      students: {
        Row: {
          id: string
          [key: string]: unknown
        }
        Insert: {
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
      teachers: {
        Row: {
          id: string
          [key: string]: unknown
        }
        Insert: {
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
      bookings: {
        Row: {
          id: string
          student_id: string
          teacher_id: string
          scheduled_start: string
          scheduled_end: string
          status: string
          [key: string]: unknown
        }
        Insert: {
          student_id: string
          teacher_id: string
          scheduled_start: string
          scheduled_end: string
          contract_id?: string
          zoom_account_id?: string
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
      student_contracts: {
        Row: {
          id: string
          [key: string]: unknown
        }
        Insert: {
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
      teacher_contracts: {
        Row: {
          id: string
          [key: string]: unknown
        }
        Insert: {
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
      zoom_accounts: {
        Row: {
          id: string
          [key: string]: unknown
        }
        Insert: {
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
      line_user_bindings: {
        Row: {
          id: string
          user_id: string
          line_user_id: string
          line_display_name: string | null
          line_picture_url: string | null
          line_email: string | null
          binding_status: string
          channel_type: string
          notify_booking_confirmation: boolean
          notify_booking_reminder: boolean
          notify_status_update: boolean
          bound_at: string
          created_at: string
          updated_at: string
        }
        Insert: {
          user_id: string
          line_user_id: string
          [key: string]: unknown
        }
        Update: {
          [key: string]: unknown
        }
      }
    }
    Views: {
      v_active_students: {
        Row: {
          [key: string]: unknown
        }
      }
      v_active_teachers: {
        Row: {
          [key: string]: unknown
        }
      }
      v_active_bookings: {
        Row: {
          [key: string]: unknown
        }
      }
    }
    Functions: {
      [key: string]: unknown
    }
    Enums: {
      [key: string]: unknown
    }
  }
}

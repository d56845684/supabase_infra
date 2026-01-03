import { defineStore } from 'pinia';
import { nanoid } from 'nanoid';
import type { UserProfile, UserRole } from '@/types/schema';
import { supabase } from '@/lib/supabase';

interface SessionMeta {
  userId: string;
  sessionId: string;
}

const ACTIVE_SESSION_KEY = 'teaching-platform-active-session';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    currentUser: null as UserProfile | null,
    sessionId: ''
  }),
  getters: {
    isLoggedIn: (state) => !!state.currentUser,
    defaultRoute: (state) => {
      const role = state.currentUser?.role;
      switch (role) {
        case 'admin':
          return '/system/accounts';
        case 'teacher':
          return '/courses/overview';
        case 'student':
          return '/students/bookings';
        default:
          return '/login';
      }
    }
  },
  actions: {
    async restoreSession() {
      if (this.currentUser) return;
      const existing = this.readSession();
      const { data } = await supabase.auth.getSession();
      const userId = existing?.userId ?? data.session?.user.id;
      if (!userId) return;

      if (existing) {
        this.sessionId = existing.sessionId;
      }

      await this.loadUser(userId);

      if (!existing) {
        this.sessionId = await this.persistSession(userId);
      }
    },
    async loginWithEmail(email: string, password: string) {
      const { data, error } = await supabase.auth.signInWithPassword({ email, password });
      if (error) throw error;
      const userId = data.session?.user.id;
      if (!userId) throw new Error('登入失敗，請稍後再試');

      const active = this.readSession();
      if (active && active.userId === userId && active.sessionId !== this.sessionId) {
        throw new Error('同帳號已有其他登入工作階段');
      }

      await this.loadUser(userId);
      this.sessionId = await this.persistSession(userId);
    },
    async loadUser(userId: string) {
      const { data, error } = await supabase.from('user_profiles').select('*').eq('id', userId).single();
      if (error) throw error;
      this.currentUser = data as UserProfile;
    },
    async logout() {
      const active = this.readSession();
      if (active && active.sessionId === this.sessionId) {
        localStorage.removeItem(ACTIVE_SESSION_KEY);
      }
      await supabase.auth.signOut();
      this.currentUser = null;
      this.sessionId = '';
    },
    async persistSession(userId: string) {
      const sessionId = nanoid();
      const session: SessionMeta = { userId, sessionId };
      localStorage.setItem(ACTIVE_SESSION_KEY, JSON.stringify(session));
      await supabase.from('active_sessions').upsert({ user_id: userId, session_id: sessionId });
      return sessionId;
    },
    readSession(): SessionMeta | null {
      const raw = localStorage.getItem(ACTIVE_SESSION_KEY);
      if (!raw) return null;
      try {
        return JSON.parse(raw) as SessionMeta;
      } catch (error) {
        console.error('Failed to parse session', error);
        return null;
      }
    },
    canAccessRole(role: UserRole, allowed?: UserRole[]) {
      if (!allowed || allowed.length === 0) return true;
      return allowed.includes(role);
    }
  }
});

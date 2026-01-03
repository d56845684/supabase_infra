import { defineStore } from 'pinia';
import { nanoid } from 'nanoid';
import type { UserProfile, UserRole } from '@/types/schema';

interface SessionMeta {
  userId: string;
  sessionId: string;
}

const ACTIVE_SESSION_KEY = 'teaching-platform-active-session';

const seedUsers: UserProfile[] = [
  {
    id: 'admin-1',
    role: 'admin',
    fullName: 'Admin User',
    email: 'admin@example.com',
    phone: '+886900111222'
  },
  {
    id: 'teacher-1',
    role: 'teacher',
    fullName: 'Teacher Jane',
    email: 'teacher@example.com'
  },
  {
    id: 'student-1',
    role: 'student',
    fullName: 'Student Ray',
    email: 'student@example.com'
  }
];

export const useAuthStore = defineStore('auth', {
  state: () => ({
    currentUser: null as UserProfile | null,
    sessionId: ''
  }),
  actions: {
    autoLogin() {
      if (!this.currentUser) {
        this.currentUser = seedUsers[0];
        this.sessionId = this.persistSession(this.currentUser.id);
      }
    },
    login(userId: string, role: UserRole) {
      const found = seedUsers.find((u) => u.id === userId && u.role === role);
      if (!found) throw new Error('User not found');

      const active = this.readSession();
      if (active && active.userId === userId && active.sessionId !== this.sessionId) {
        throw new Error('同帳號已有其他登入工作階段');
      }

      this.currentUser = found;
      this.sessionId = this.persistSession(userId);
    },
    logout() {
      const active = this.readSession();
      if (active && active.sessionId === this.sessionId) {
        localStorage.removeItem(ACTIVE_SESSION_KEY);
      }
      this.currentUser = null;
      this.sessionId = '';
    },
    persistSession(userId: string) {
      const sessionId = nanoid();
      const session: SessionMeta = { userId, sessionId };
      localStorage.setItem(ACTIVE_SESSION_KEY, JSON.stringify(session));
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
    }
  }
});

import { defineStore } from 'pinia';

export const useThemeStore = defineStore('theme', {
  state: () => ({
    isDark: false
  }),
  actions: {
    toggleTheme() {
      this.isDark = !this.isDark;
      this.applyTheme();
    },
    setDark(value: boolean) {
      this.isDark = value;
      this.applyTheme();
    },
    applyTheme() {
      const body = document.documentElement;
      body.classList.toggle('dark', this.isDark);
    }
  }
});

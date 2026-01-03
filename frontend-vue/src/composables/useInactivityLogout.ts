import { onMounted, onUnmounted } from 'vue';

interface Options {
  timeoutMs?: number;
  onTimeout: () => void;
}

export function useInactivityLogout({ timeoutMs = 10 * 60 * 1000, onTimeout }: Options) {
  let timer: number | null = null;

  const resetTimer = () => {
    if (timer) window.clearTimeout(timer);
    timer = window.setTimeout(onTimeout, timeoutMs);
  };

  const activityEvents = ['mousemove', 'keydown', 'click', 'touchstart'];

  onMounted(() => {
    activityEvents.forEach((event) => window.addEventListener(event, resetTimer));
    resetTimer();
  });

  onUnmounted(() => {
    if (timer) window.clearTimeout(timer);
    activityEvents.forEach((event) => window.removeEventListener(event, resetTimer));
  });

  return { resetTimer };
}

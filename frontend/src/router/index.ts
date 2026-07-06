import { createRouter, createWebHistory } from 'vue-router'

// Routes are lazy-loaded so each view ships in its own chunk (performance).
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
  ],
})

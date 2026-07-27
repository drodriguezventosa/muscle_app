import { createRouter, createWebHistory } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

// Routes are lazy-loaded so each view ships in its own chunk (performance).
export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'explorer',
      component: () => import('@/views/ExplorerView.vue'),
    },
    {
      path: '/workouts',
      name: 'workouts',
      component: () => import('@/views/WorkoutsView.vue'),
    },
    {
      path: '/nutrition',
      name: 'nutrition',
      component: () => import('@/views/NutritionView.vue'),
    },
    {
      path: '/progress',
      name: 'progress',
      component: () => import('@/views/ProgressView.vue'),
    },
    {
      path: '/login',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
    },
    {
      path: '/trainers',
      name: 'trainers',
      component: () => import('@/views/TrainersView.vue'),
    },
  ],
})

// Routes flagged with `meta.requiresAuth` need a signed-in user; the intended
// path travels as `redirect` so the user lands where they meant to go.
router.beforeEach((to) => {
  if (!to.meta.requiresAuth) return true
  // Called inside the guard (not at module scope) so Pinia is already installed.
  return useAuthStore().isSignedIn ? true : { name: 'login', query: { redirect: to.fullPath } }
})

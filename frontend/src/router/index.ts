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
      path: '/students',
      name: 'students',
      // Trainer-only: the guard below sends anyone else to the sign-in modal.
      meta: { requiresAuth: true, role: 'trainer' },
      component: () => import('@/views/StudentsView.vue'),
    },
    {
      path: '/plan',
      name: 'plan',
      // The student's own calendar; a trainer has their students' instead.
      meta: { requiresAuth: true, role: 'client' },
      component: () => import('@/views/PlanView.vue'),
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
  const auth = useAuthStore()
  if (auth.isSignedIn) {
    // Signed in but with the wrong role: send them to their own area.
    if (to.meta.role && to.meta.role !== auth.user?.role) return { path: '/' }
    return true
  }
  // Sign-in is a modal, not a page: block the navigation and open it, keeping
  // the intended route so the user lands there afterwards.
  auth.promptSignIn(to.fullPath)
  return false
})

import type { TourStep } from '@/components/GuidedTour.vue'

/** What the visitor may see, which is what decides the coaching part of the tour. */
export interface TourAudience {
  isSignedIn: boolean
  isTrainer: boolean
  hasTrainer: boolean
}

const MAIN = '[data-tour="main"]'

/**
 * The guided tour, built for one audience.
 *
 * A step that navigates must only ever go somewhere this visitor can actually
 * go: the coaching area is role-gated, so a trainer is walked through their
 * students, a student with a trainer through their plan, and everyone else is
 * told what those are and how to reach them (no route, no dead end).
 *
 * Kept as a pure function so the composition is testable without mounting the
 * app — the interesting part is which steps exist for whom.
 */
export function buildTourSteps(audience: TourAudience): TourStep[] {
  const coaching: TourStep[] = audience.isTrainer
    ? [
        { route: '/students', target: MAIN, ...keys('students') },
        { route: '/students', target: MAIN, ...keys('studentPlan') },
      ]
    : [
        { route: '/trainers', target: MAIN, ...keys('trainers') },
        audience.hasTrainer
          ? { route: '/plan', target: MAIN, ...keys('plan') }
          : keys('planPreview'),
      ]

  return [
    { route: '/', ...keys('welcome') },
    { route: '/', target: MAIN, ...keys('explore') },
    { route: '/workouts', target: MAIN, ...keys('workouts') },
    { route: '/nutrition', target: MAIN, ...keys('nutrition') },
    { route: '/nutrition', target: '[data-tour="meal-photo"]', ...keys('mealPhoto') },
    { route: '/progress', target: MAIN, ...keys('progress') },
    ...coaching,
    ...(audience.isSignedIn ? [] : [keys('signIn')]),
    { target: '[data-testid="chat-toggle"]', ...keys('assistant') },
    { target: '[data-tour="theme"]', ...keys('controls') },
    keys('done'),
  ]
}

/** The two translation keys of a step, which always follow its name. */
function keys(step: string): { titleKey: string; bodyKey: string } {
  return { titleKey: `tour.steps.${step}.title`, bodyKey: `tour.steps.${step}.body` }
}

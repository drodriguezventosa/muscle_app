import { describe, expect, it } from 'vitest'

import en from '@/i18n/locales/en'
import es from '@/i18n/locales/es'
import { buildTourSteps, type TourAudience } from '@/tour/steps'

const ANONYMOUS: TourAudience = { isSignedIn: false, isTrainer: false, hasTrainer: false }
const STUDENT: TourAudience = { isSignedIn: true, isTrainer: false, hasTrainer: true }
const STUDENT_ALONE: TourAudience = { isSignedIn: true, isTrainer: false, hasTrainer: false }
const TRAINER: TourAudience = { isSignedIn: true, isTrainer: true, hasTrainer: false }

/** Resolve a dotted key against a locale object, or undefined if it is missing. */
function lookup(locale: object, key: string): unknown {
  return key.split('.').reduce<unknown>((node, part) => {
    if (node && typeof node === 'object' && part in node) {
      return (node as Record<string, unknown>)[part]
    }
    return undefined
  }, locale)
}

describe('guided tour steps', () => {
  it.each([
    ['anonymous', ANONYMOUS],
    ['student', STUDENT],
    ['student without a trainer', STUDENT_ALONE],
    ['trainer', TRAINER],
  ])('is fully translated in both languages for a %s', (_name, audience) => {
    for (const step of buildTourSteps(audience)) {
      for (const key of [step.titleKey, step.bodyKey]) {
        expect(typeof lookup(es, key), `es: ${key}`).toBe('string')
        expect(typeof lookup(en, key), `en: ${key}`).toBe('string')
      }
    }
  })

  it('covers every section of the app', () => {
    const routes = buildTourSteps(ANONYMOUS).map((step) => step.route)
    expect(routes).toContain('/workouts')
    expect(routes).toContain('/nutrition')
    expect(routes).toContain('/progress')
    expect(routes).toContain('/trainers')
  })

  it('explains the meal photo, which is easy to miss inside nutrition', () => {
    const steps = buildTourSteps(ANONYMOUS)
    const photo = steps.find((step) => step.titleKey.includes('mealPhoto'))
    expect(photo?.target).toBe('[data-tour="meal-photo"]')
    expect(photo?.route).toBe('/nutrition')
  })

  it('walks a trainer through their students, not through hiring one', () => {
    const steps = buildTourSteps(TRAINER)
    expect(steps.map((step) => step.route)).toContain('/students')
    // Hiring is not something a trainer can do, so that step is not for them.
    expect(steps.map((step) => step.titleKey)).not.toContain('tour.steps.trainers.title')
    expect(steps.map((step) => step.route)).not.toContain('/plan')
  })

  it('walks a student with a trainer through their plan', () => {
    const steps = buildTourSteps(STUDENT)
    expect(steps.map((step) => step.route)).toContain('/plan')
    expect(steps.map((step) => step.titleKey)).not.toContain('tour.steps.planPreview.title')
  })

  it('never sends a visitor to a page their role cannot open', () => {
    // A route-gated step would open the sign-in modal mid-tour, or bounce.
    const gated = ['/plan', '/students']
    for (const audience of [ANONYMOUS, STUDENT_ALONE]) {
      const routes = buildTourSteps(audience).map((step) => step.route)
      expect(routes.filter((route) => route && gated.includes(route))).toEqual([])
    }
  })

  it('offers signing in only to visitors who are not', () => {
    const titles = (audience: TourAudience) =>
      buildTourSteps(audience).map((step) => step.titleKey)
    expect(titles(ANONYMOUS)).toContain('tour.steps.signIn.title')
    expect(titles(STUDENT)).not.toContain('tour.steps.signIn.title')
  })
})

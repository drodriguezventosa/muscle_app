import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'

import LanguageSwitcher from '@/components/LanguageSwitcher.vue'
import { i18n } from '@/i18n'

describe('LanguageSwitcher', () => {
  afterEach(() => {
    i18n.global.locale.value = 'es'
  })

  it('opens the menu and switches the active locale', async () => {
    i18n.global.locale.value = 'es'
    const wrapper = mount(LanguageSwitcher, { global: { plugins: [i18n] } })

    await wrapper.get('.current').trigger('click')
    const english = wrapper.findAll('[role="option"]').find((o) => o.text().includes('English'))
    expect(english).toBeTruthy()

    await english!.trigger('click')
    expect(i18n.global.locale.value).toBe('en')
  })
})

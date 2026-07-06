import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import HomeView from '@/views/HomeView.vue'

describe('HomeView', () => {
  it('renders the hero heading', () => {
    const wrapper = mount(HomeView)
    expect(wrapper.find('h1').exists()).toBe(true)
  })

  it('always shows the medical disclaimer', () => {
    const wrapper = mount(HomeView)
    expect(wrapper.find('[role="note"]').exists()).toBe(true)
  })
})

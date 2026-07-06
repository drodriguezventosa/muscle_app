import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import VideoModal from '@/components/VideoModal.vue'
import { i18n } from '@/i18n'

describe('VideoModal', () => {
  it('builds a privacy-friendly embed URL from a watch URL', () => {
    const wrapper = mount(VideoModal, {
      props: { url: 'https://www.youtube.com/watch?v=WDIpL0pjun0', title: 'Push-up' },
      global: { plugins: [i18n], stubs: { teleport: true } },
    })
    const src = wrapper.get('iframe').attributes('src')
    expect(src).toContain('youtube-nocookie.com/embed/WDIpL0pjun0')
    expect(src).toContain('autoplay=1')
  })

  it('emits close when the close button is clicked', async () => {
    const wrapper = mount(VideoModal, {
      props: { url: 'https://www.youtube.com/watch?v=WDIpL0pjun0', title: 'Push-up' },
      global: { plugins: [i18n], stubs: { teleport: true } },
    })
    await wrapper.get('.close').trigger('click')
    expect(wrapper.emitted('close')).toBeTruthy()
  })
})

import { onBeforeUnmount, onMounted, ref, type Ref } from 'vue'

/**
 * Track an element's width in CSS pixels.
 *
 * Charts draw in real pixels rather than scaling a fixed `viewBox`: with a
 * scaled viewBox the labels shrink with the container, which on a phone leaves
 * axis text at half its intended size.
 */
export function useElementWidth(element: Ref<HTMLElement | null>, fallback = 640) {
  const width = ref(fallback)
  let observer: ResizeObserver | null = null

  onMounted(() => {
    if (!element.value) return
    // Not in jsdom, and not in older browsers: the fallback width keeps the
    // chart renderable instead of collapsing it to nothing.
    if (typeof ResizeObserver === 'undefined') {
      width.value = element.value.clientWidth || fallback
      return
    }
    observer = new ResizeObserver(([entry]) => {
      const measured = entry.contentRect.width
      if (measured > 0) width.value = measured
    })
    observer.observe(element.value)
  })

  onBeforeUnmount(() => observer?.disconnect())

  return width
}

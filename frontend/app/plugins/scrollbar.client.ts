import { OverlayScrollbars } from 'overlayscrollbars'
import 'overlayscrollbars/overlayscrollbars.css'

export default defineNuxtPlugin((nuxtApp) => {
  const instances = new Map<HTMLElement, ReturnType<typeof OverlayScrollbars>>()

  const initContainer = (element: HTMLElement) => {
    if (instances.has(element)) return

    const instance = OverlayScrollbars(
      {
        target: element,
        elements: {
          viewport: element.firstElementChild as HTMLElement | undefined,
        },
      },
      {
        scrollbars: {
          autoHide: 'move',
          autoHideDelay: 400,
          clickScroll: true,
        },
      },
    )

    instances.set(element, instance)
  }

  const initAll = () => {
    document
      .querySelectorAll<HTMLElement>('[data-os-root]')
      .forEach((element) => initContainer(element))
  }

  nuxtApp.hook('app:mounted', () => {
    initAll()

    const observer = new MutationObserver(() => initAll())
    observer.observe(document.body, { childList: true, subtree: true })

    window.addEventListener('beforeunload', () => {
      observer.disconnect()
      instances.forEach((instance) => instance.destroy())
      instances.clear()
    })
  })
})

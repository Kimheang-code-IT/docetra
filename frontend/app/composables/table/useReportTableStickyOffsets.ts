import { onBeforeUnmount, onMounted, ref, unref, watch, type Ref } from 'vue'

export function useReportTableStickyOffsets(
  scrollRef: Ref<HTMLElement | undefined>,
  stickyCount: Ref<number> | number,
  watchSources: Ref<unknown>[] = [],
) {
  const stickyOffsets = ref<number[]>([])

  function remeasureSticky() {
    const root = scrollRef.value
    const count = unref(stickyCount)
    if (!root || count <= 0) {
      stickyOffsets.value = []
      return
    }

    const row = root.querySelector<HTMLTableRowElement>('tbody tr.app-report-table__row')
    if (!row) return

    const cells = Array.from(row.cells)
    const next: number[] = []
    let acc = 0
    for (let i = 0; i < count && i < cells.length; i++) {
      next.push(acc)
      acc += cells[i]!.getBoundingClientRect().width
    }
    stickyOffsets.value = next
  }

  let observer: ResizeObserver | undefined

  onMounted(() => {
    remeasureSticky()
    const root = scrollRef.value
    if (!root) return

    observer = new ResizeObserver(() => remeasureSticky())
    observer.observe(root)
    const table = root.querySelector('table')
    if (table) observer.observe(table)
  })

  onBeforeUnmount(() => {
    observer?.disconnect()
  })

  if (watchSources.length) {
    watch(watchSources, () => {
      requestAnimationFrame(remeasureSticky)
    }, { flush: 'post' })
  }

  return { stickyOffsets, remeasureSticky }
}

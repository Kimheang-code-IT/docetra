interface PointerDropOptions {
  selector: string
  dataKey: string
  onDragStart: () => void
  onDrop: (value: string) => void
  onDragEnd: () => void
}

/** Adds touch/pen dragging alongside native mouse drag and drop. */
export function usePointerDrop(options: PointerDropOptions) {
  let pointerId: number | null = null
  let startX = 0
  let startY = 0
  let dragging = false
  let suppressClick = false

  function onPointerDown(event: PointerEvent) {
    if (event.pointerType === 'mouse') return
    const target = event.target as HTMLElement | null
    if (target?.closest('button, a, input, textarea, select, [role="menuitem"]')) return

    pointerId = event.pointerId
    startX = event.clientX
    startY = event.clientY
    ;(event.currentTarget as HTMLElement | null)?.setPointerCapture?.(event.pointerId)
  }

  function onPointerMove(event: PointerEvent) {
    if (pointerId !== event.pointerId) return
    if (!dragging && Math.hypot(event.clientX - startX, event.clientY - startY) < 8) return

    if (!dragging) {
      dragging = true
      options.onDragStart()
    }
    event.preventDefault()
  }

  function finishPointer(event: PointerEvent, cancelled = false) {
    if (pointerId !== event.pointerId) return

    if (dragging) {
      if (!cancelled) {
        const target = document.elementFromPoint(event.clientX, event.clientY) as HTMLElement | null
        const dropTarget = target?.closest<HTMLElement>(options.selector)
        const value = dropTarget?.dataset[options.dataKey]
        if (value != null) options.onDrop(value)
      }

      suppressClick = true
      options.onDragEnd()
      requestAnimationFrame(() => { suppressClick = false })
    }

    pointerId = null
    dragging = false
  }

  function onPointerUp(event: PointerEvent) {
    finishPointer(event)
  }

  function onPointerCancel(event: PointerEvent) {
    finishPointer(event, true)
  }

  function onClick(event: MouseEvent) {
    if (!suppressClick) return false
    event.preventDefault()
    event.stopPropagation()
    return true
  }

  return {
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onPointerCancel,
    onClick,
  }
}

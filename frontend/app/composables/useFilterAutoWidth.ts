const MIN_WIDTH_PX = 120 // compact dashboard-style pill
const MAX_WIDTH_PX = 520
const CHROME_PX = 52 // trailing chevron + horizontal padding (no leading icon by default)

let measureEl: HTMLSpanElement | null = null

function measureTextWidth(text: string): number {
  if (typeof document === 'undefined' || !text) return 0

  if (!measureEl) {
    measureEl = document.createElement('span')
    measureEl.setAttribute('aria-hidden', 'true')
    Object.assign(measureEl.style, {
      position: 'absolute',
      visibility: 'hidden',
      whiteSpace: 'nowrap',
      pointerEvents: 'none',
      fontSize: '13px',
      fontWeight: '500',
      fontFamily: 'inherit',
    })
    document.body.appendChild(measureEl)
  }

  measureEl.textContent = text
  return Math.ceil(measureEl.getBoundingClientRect().width)
}

/**
 * Compact min width with growth so the trigger can show the full filter/sort title.
 */
export function useFilterAutoWidth(
  label: MaybeRefOrGetter<string | undefined>,
  placeholder: MaybeRefOrGetter<string | undefined>,
  displayValue?: MaybeRefOrGetter<string | undefined>,
) {
  const widthPx = ref(MIN_WIDTH_PX)

  function recompute() {
    const candidates = [
      toValue(label),
      toValue(placeholder),
      toValue(displayValue),
    ].filter((v): v is string => Boolean(v && String(v).trim()))

    const content = Math.max(0, ...candidates.map(measureTextWidth))
    widthPx.value = Math.min(MAX_WIDTH_PX, Math.max(MIN_WIDTH_PX, content + CHROME_PX))
  }

  watch(
    () => [toValue(label), toValue(placeholder), toValue(displayValue)] as const,
    () => recompute(),
    { immediate: true },
  )

  onMounted(() => recompute())

  const widthStyle = computed(() => ({
    width: `${widthPx.value}px`,
    minWidth: `${MIN_WIDTH_PX}px`,
    maxWidth: `${MAX_WIDTH_PX}px`,
  }))

  const rootClass = 'shrink-0'

  return { widthStyle, rootClass, widthPx }
}

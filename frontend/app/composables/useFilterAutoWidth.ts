import { computed, type MaybeRefOrGetter, toValue } from 'vue'

const MIN_REM = 11
const MAX_REM = 24

/** Estimate filter control width from visible title text (supports Khmer / Latin). */
export function useFilterAutoWidth(
  label: MaybeRefOrGetter<string | undefined>,
  fallback?: MaybeRefOrGetter<string | undefined>,
) {
  const widthStyle = computed(() => {
    const text = toValue(label) || toValue(fallback) || ''
    if (!text) {
      return { minWidth: `${MIN_REM}rem` }
    }

    const length = [...text].length
    const rem = Math.min(Math.max(length * 0.55 + 2.5, MIN_REM), MAX_REM)

    return {
      minWidth: `${rem}rem`,
      width: 'max-content',
    }
  })

  const rootClass = 'inline-flex flex-col gap-0.5 shrink-0 max-w-72'

  return { widthStyle, rootClass }
}

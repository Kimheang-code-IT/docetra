import { computed, type ComputedRef, type MaybeRefOrGetter, toValue } from 'vue'

export function useReactiveChartData<T, R>(
  source: MaybeRefOrGetter<T[]>,
  build: (rows: T[]) => R,
): ComputedRef<R | null> {
  return computed(() => {
    const rows = toValue(source)
    if (!rows.length) return null
    return build(rows)
  })
}

export function useChartLoadingState(
  pending: MaybeRefOrGetter<boolean>,
  data: MaybeRefOrGetter<unknown | null | undefined>,
) {
  return computed(() => {
    if (toValue(pending)) return 'loading' as const
    if (!toValue(data)) return 'empty' as const
    return 'ready' as const
  })
}

export function shouldDisableChartAnimation(pointCount: number, threshold = 80) {
  return pointCount >= threshold
}

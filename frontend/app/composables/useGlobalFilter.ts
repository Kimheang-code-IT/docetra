import { computed } from 'vue'
import { parseDate, type DateValue } from '@internationalized/date'
import { useState } from '#app'

type GlobalDateRangeState = {
  start: string | null
  end: string | null
}

type CalendarDateRange = {
  start: DateValue | undefined
  end: DateValue | undefined
}

/**
 * Cross-page date range filter (SSR-safe via useState).
 * Consumed by table API params, analytics, export, and import filters.
 */
export function useGlobalFilter() {
  const state = useState<GlobalDateRangeState>('globalDateRange', () => ({
    start: null,
    end: null,
  }))

  const dateRange = computed({
    get: (): CalendarDateRange => ({
      start: state.value.start ? parseDate(state.value.start) : undefined,
      end: state.value.end ? parseDate(state.value.end) : undefined,
    }),
    set: (val: CalendarDateRange | null | undefined) => {
      state.value = {
        start: val?.start ? String(val.start) : null,
        end: val?.end ? String(val.end) : null,
      }
    },
  })

  const formattedRange = computed(() => ({
    start: state.value.start || '',
    end: state.value.end || '',
  }))

  const hasDateRange = computed(() =>
    Boolean(state.value.start || state.value.end),
  )

  function resetRange() {
    state.value = { start: null, end: null }
  }

  /** Inclusive YYYY-MM-DD check against the shared range. */
  function isDateInRange(dateValue?: string | null): boolean {
    if (!hasDateRange.value) return true
    if (!dateValue) return false

    const day = String(dateValue).slice(0, 10)
    const { start, end } = state.value
    if (start && day < start) return false
    if (end && day > end) return false
    return true
  }

  return {
    dateRange,
    formattedRange,
    hasDateRange,
    resetRange,
    isDateInRange,
  }
}

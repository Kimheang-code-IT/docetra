import type { ComputedRef, MaybeRefOrGetter, Ref, WritableComputedRef } from 'vue'
import { computed, ref, toValue } from 'vue'
import { parseDate } from '@internationalized/date'

function toDayKey(value: string | undefined): string | null {
  if (!value) return null
  const raw = String(value).trim()
  if (!raw) return null

  const isoDay = raw.slice(0, 10)
  if (/^\d{4}-\d{2}-\d{2}$/.test(isoDay)) return isoDay

  const parsed = new Date(raw)
  if (Number.isNaN(parsed.getTime())) return null

  const year = parsed.getFullYear()
  const month = String(parsed.getMonth() + 1).padStart(2, '0')
  const day = String(parsed.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function useChartDuration<T>(
  source: MaybeRefOrGetter<T[]>,
  getRowDate: (row: T) => string | undefined,
): {
  dateRange: WritableComputedRef<{ start: any; end: any }>
  durationRows: ComputedRef<T[]>
  resetRange: () => void
} {
  const state = ref<{ start: string | null; end: string | null }>({
    start: null,
    end: null,
  })

  const dateRange = computed({
    get: () => ({
      start: state.value.start ? parseDate(state.value.start) : undefined,
      end: state.value.end ? parseDate(state.value.end) : undefined,
    }),
    set: (val: { start?: { toString: () => string } | null; end?: { toString: () => string } | null } | null) => {
      state.value = {
        start: val?.start ? val.start.toString().slice(0, 10) : null,
        end: val?.end ? val.end.toString().slice(0, 10) : null,
      }
    },
  })

  const rows = computed(() => toValue(source))

  const durationRows = computed(() => {
    const startKey = state.value.start
    const endKey = state.value.end

    if (!startKey && !endKey) return rows.value

    return rows.value.filter((row) => {
      const dayKey = toDayKey(getRowDate(row))
      if (!dayKey) return false
      if (startKey && dayKey < startKey) return false
      if (endKey && dayKey > endKey) return false
      return true
    })
  })

  function resetRange() {
    state.value = { start: null, end: null }
  }

  return {
    dateRange,
    durationRows,
    resetRange,
  }
}

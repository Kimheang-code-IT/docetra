import {
  CalendarDate,
  CalendarDateTime,
  Time,
  parseDate,
  parseDateTime,
} from '@internationalized/date'
import type { DateValue } from '@internationalized/date'

export type DatePickerGranularity = 'day' | 'hour' | 'minute' | 'second'

/** Anchor popover to input start (left), not centered on screen. */
export const datePickerPopoverContent = {
  side: 'bottom' as const,
  align: 'start' as const,
  sideOffset: 4,
  alignOffset: 0,
  collisionPadding: 8,
}

export function isDateTimeGranularity(granularity: DatePickerGranularity) {
  return granularity !== 'day'
}

export function parsePickerValue(
  value?: string | null,
  isDateTime = false,
): DateValue | undefined {
  if (!value) return undefined
  try {
    if (isDateTime) {
      const normalized = value.includes('T')
        ? value.slice(0, 16)
        : `${value.slice(0, 10)}T00:00`
      return parseDateTime(normalized)
    }
    return parseDate(value.slice(0, 10))
  }
  catch {
    return undefined
  }
}

export function serializePickerValue(value?: DateValue | null): string {
  if (!value) return ''
  if ('hour' in value) {
    const dt = value as CalendarDateTime
    const hh = String(dt.hour).padStart(2, '0')
    const mm = String(dt.minute).padStart(2, '0')
    return `${dt.toString().slice(0, 10)}T${hh}:${mm}`
  }
  return value.toString()
}

/** Persist filter ranges as `YYYY-MM-DD` only — never a time. */
export function serializeDateOnly(value?: DateValue | null): string {
  if (!value) return ''
  const year = String(value.year).padStart(4, '0')
  const month = String(value.month).padStart(2, '0')
  const day = String(value.day).padStart(2, '0')
  return `${year}-${month}-${day}`
}

export function toDateOnlyString(value?: string | null): string {
  const day = String(value || '').trim().slice(0, 10)
  return /^\d{4}-\d{2}-\d{2}$/.test(day) ? day : ''
}

/** Day-first calendar locale so filter fields show `dd/mm/yyyy`, not time. */
export function dateFilterFieldLocale(uiLocale?: string): string {
  if (String(uiLocale || '').toLowerCase().startsWith('km')) return 'km-KH'
  return 'en-GB'
}

export function toCalendarDate(value?: DateValue | null): CalendarDate | undefined {
  if (!value) return undefined
  return new CalendarDate(value.year, value.month, value.day)
}

export function mergeDateWithTime(
  date: CalendarDate,
  current?: DateValue | null,
  fallbackHour = 0,
  fallbackMinute = 0,
): DateValue {
  if (current && 'hour' in current) {
    return new CalendarDateTime(date.year, date.month, date.day, current.hour, current.minute)
  }
  return new CalendarDateTime(date.year, date.month, date.day, fallbackHour, fallbackMinute)
}

export function parseTimeValue(value?: string | null): Time | undefined {
  const parsed = parsePickerValue(value, true)
  if (parsed && 'hour' in parsed) {
    const dt = parsed as CalendarDateTime
    return new Time(dt.hour, dt.minute, 0)
  }
  return undefined
}

export function mergeCalendarDateAndTime(
  date: CalendarDate | undefined | null,
  time?: Time | null,
): string {
  if (!date) return ''
  const hour = time?.hour ?? 0
  const minute = time?.minute ?? 0
  return serializePickerValue(new CalendarDateTime(date.year, date.month, date.day, hour, minute))
}

/** ERPNext-style form fields: fill, no idle border, grey ring when focused. */
export function getFormDateUi(fullWidth = true) {
  return {
    base: [
      fullWidth ? 'w-full min-w-0' : '',
      'shadow-none outline-none ring-0 has-focus:ring-1 has-focus:ring-inset has-focus:ring-default has-focus-visible:outline-none',
    ].filter(Boolean).join(' '),
    trailing: 'pe-0.5',
    trailingIcon: 'text-muted',
  }
}


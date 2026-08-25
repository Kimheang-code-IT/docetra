import { describe, expect, it } from 'vitest'
import { CalendarDate, CalendarDateTime } from '@internationalized/date'
import {
  dateFilterFieldLocale,
  parsePickerValue,
  serializeDateOnly,
  toDateOnlyString,
} from '../../app/utils/date-picker'

describe('date filter helpers', () => {
  it('stores filter values as YYYY-MM-DD with no time', () => {
    const date = new CalendarDate(2026, 8, 25)
    expect(serializeDateOnly(date)).toBe('2026-08-25')
    expect(serializeDateOnly(new CalendarDateTime(2026, 8, 25, 14, 30))).toBe('2026-08-25')
  })

  it('strips time from existing filter strings', () => {
    expect(toDateOnlyString('2026-08-25T14:30')).toBe('2026-08-25')
    expect(toDateOnlyString('2026-08-25T00:00:00.000Z')).toBe('2026-08-25')
    expect(toDateOnlyString('2026-08-25')).toBe('2026-08-25')
    expect(toDateOnlyString('')).toBe('')
  })

  it('parses filter values as calendar dates, not datetimes', () => {
    const parsed = parsePickerValue('2026-08-25T14:30', false)
    expect(parsed).toBeInstanceOf(CalendarDate)
    expect(serializeDateOnly(parsed)).toBe('2026-08-25')
  })

  it('uses a day-first locale so the field shows dd/mm/yyyy', () => {
    expect(dateFilterFieldLocale('en')).toBe('en-GB')
    expect(dateFilterFieldLocale('km')).toBe('km-KH')
  })
})

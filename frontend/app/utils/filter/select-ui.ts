/**
 * Shared Nuxt UI styles for toolbar / dashboard filter pills and live search.
 * Idle: subtle ring. Active (has value): primary ring so selection is visible.
 */

const selectChrome = 'rounded-lg bg-elevated font-medium text-highlighted'
const selectIdle = `${selectChrome} ring-1 ring-default`
const selectActive = `${selectChrome} ring-1 ring-primary bg-primary/5`

export const filterSelectUi = {
  base: selectIdle,
  value: 'truncate',
  trailingIcon: 'text-muted',
  content: 'max-h-60 min-w-(--reka-combobox-trigger-width)',
} as const

export function getFilterSelectUi(active: boolean) {
  return {
    ...filterSelectUi,
    base: active ? selectActive : selectIdle,
  }
}

const searchIdle = 'rounded-md bg-default ring-1 ring-default focus-visible:ring-2 focus-visible:ring-primary/30'
const searchActive = 'rounded-md bg-default ring-1 ring-primary bg-primary/5 focus-visible:ring-2 focus-visible:ring-primary/30'

export function getFilterSearchUi(active: boolean) {
  return {
    base: active ? searchActive : searchIdle,
  }
}

export function isFilterValueActive(value: unknown): boolean {
  if (value == null || value === '') return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'string') return value.trim().length > 0
  return true
}

/**
 * Shared Nuxt UI styles for toolbar / dashboard filter pills and live search.
 * Active border uses default grey (`ring-default`), not inverted/black.
 */

const selectChrome = 'rounded-lg bg-elevated/70 font-medium text-highlighted'
const selectIdle = `${selectChrome} ring-0`
const selectActive = `${selectChrome} ring-1 ring-inset ring-default`

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

export function getFilterSearchUi(active: boolean) {
  return {
    base: active
      ? 'rounded-md bg-elevated/70 ring-1 ring-inset ring-default'
      : 'rounded-md bg-elevated/70 ring-0 focus-visible:ring-1 focus-visible:ring-inset focus-visible:ring-default',
  }
}

export function getFilterDateUi(
  active: boolean,
  options?: { isDateTime?: boolean, isRange?: boolean, fitContent?: boolean },
) {
  const chrome = active
    ? 'rounded-md bg-elevated/70 ring-1 ring-inset ring-default'
    : 'rounded-md bg-elevated/70 ring-0 has-focus:ring-1 has-focus:ring-inset has-focus:ring-default'

  const segment = options?.isDateTime
    ? [
        'data-[segment=hour]:min-w-7',
        'data-[segment=minute]:min-w-7',
        'data-[segment=dayPeriod]:min-w-8',
      ].join(' ')
    : undefined

  const width = options?.fitContent
    ? 'w-auto max-w-full pe-6'
    : 'w-full min-w-0'

  return {
    base: `${chrome} ${width}`,
    segment,
    trailing: 'pe-0',
  }
}

export function isFilterValueActive(value: unknown): boolean {
  if (value == null || value === '') return false
  if (Array.isArray(value)) return value.length > 0
  if (typeof value === 'string') return value.trim().length > 0
  return true
}

/** Shared search box config for USelectMenu / filter dropdowns. */
export function getFilterSearchInputConfig(
  t: (key: string) => string,
  placeholderKey = 'components.filterSearch',
) {
  return {
    placeholder: t(placeholderKey),
    icon: 'i-lucide-search',
    type: 'text' as const,
    autocomplete: 'off',
    class: 'app-live-search',
  }
}

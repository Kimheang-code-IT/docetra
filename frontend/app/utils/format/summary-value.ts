export function formatSummaryValue(
  raw: string | number | null | undefined,
  options: {
    prefix?: string
    suffix?: string
    decimals?: number
    formatNumber?: (value: number, fractionDigits?: number) => string
  } = {},
): string {
  const prefix = options.prefix || ''
  const suffix = options.suffix || ''
  const formatNumber = options.formatNumber || ((value: number, fractionDigits?: number) => {
    if (fractionDigits == null) return String(value)
    return value.toFixed(fractionDigits)
  })

  if (raw == null || raw === '') return '—'
  const num = typeof raw === 'number' ? raw : Number(raw)
  if (typeof raw === 'number' || (typeof raw === 'string' && raw.trim() !== '' && !Number.isNaN(num))) {
    if (Number.isNaN(num)) return '—'
    const formatted = options.decimals != null
      ? formatNumber(num, options.decimals)
      : formatNumber(num)
    return `${prefix}${formatted}${suffix}`
  }
  return `${prefix}${raw}${suffix}`
}

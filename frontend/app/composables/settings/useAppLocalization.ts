import type { AppConfigLocalization } from '~/types/docetra/settings'
import { useSettingsRepositories } from '~/repositories'

export const DEFAULT_APP_LOCALIZATION: AppConfigLocalization = {
  defaultLanguage: 'en',
  availableLanguages: ['en', 'km'],
  timezone: 'Asia/Phnom_Penh',
  dateFormat: 'YYYY-MM-DD',
  timeFormat: 'HH:mm',
  firstDayOfWeek: 1,
  numberFormat: '1,234.56',
  currency: 'USD',
  locale: 'en-US',
}

function validDate(value: unknown): Date | null {
  if (value instanceof Date) return Number.isNaN(value.getTime()) ? null : value
  if (value == null || value === '') return null
  const date = new Date(String(value))
  return Number.isNaN(date.getTime()) ? null : date
}

function dateOnlyParts(value: unknown): { year: string, month: string, day: string } | null {
  const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})(?:$|T)/)
  if (!match || String(value).includes('T')) return null
  return { year: match[1]!, month: match[2]!, day: match[3]! }
}

function configuredDateParts(date: Date, timeZone: string) {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
  }).formatToParts(date)
  const read = (type: Intl.DateTimeFormatPartTypes) => parts.find(part => part.type === type)?.value || ''
  return { year: read('year'), month: read('month'), day: read('day') }
}

function formatPattern(
  parts: { year: string, month: string, day: string },
  pattern: string,
  locale: string,
) {
  if (pattern === 'DD/MM/YYYY') return `${parts.day}/${parts.month}/${parts.year}`
  if (pattern === 'MM/DD/YYYY') return `${parts.month}/${parts.day}/${parts.year}`
  if (pattern === 'DD-MM-YYYY') return `${parts.day}-${parts.month}-${parts.year}`
  if (pattern === 'D MMM YYYY') {
    const safe = new Date(Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), 12))
    return new Intl.DateTimeFormat(locale, {
      timeZone: 'UTC',
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    }).format(safe)
  }
  return `${parts.year}-${parts.month}-${parts.day}`
}

/** Single source of truth for App Config localization on every page. */
export function useAppLocalization() {
  const localization = useState<AppConfigLocalization>('app-localization-config', () => ({
    ...DEFAULT_APP_LOCALIZATION,
    availableLanguages: [...DEFAULT_APP_LOCALIZATION.availableLanguages],
  }))
  const loaded = useState('app-localization-loaded', () => false)
  const loading = useState('app-localization-loading', () => false)

  async function load(force = false) {
    if (loaded.value && !force) return localization.value
    if (loading.value && !force) {
      await until(loading).toBe(false)
      return localization.value
    }
    loading.value = true
    try {
      const config = await useSettingsRepositories().appConfig.get()
      localization.value = {
        ...DEFAULT_APP_LOCALIZATION,
        ...(config.localization || {}),
        availableLanguages: config.localization?.availableLanguages?.length
          ? [...config.localization.availableLanguages]
          : [...DEFAULT_APP_LOCALIZATION.availableLanguages],
      }
      loaded.value = true
    }
    catch {
      loaded.value = true
    }
    finally {
      loading.value = false
    }
    return localization.value
  }

  function apply(next: Partial<AppConfigLocalization>) {
    localization.value = {
      ...localization.value,
      ...next,
      availableLanguages: next.availableLanguages?.length
        ? [...next.availableLanguages]
        : localization.value.availableLanguages,
    }
    loaded.value = true
  }

  function formatDate(value: unknown, fallback = '—') {
    const rawParts = dateOnlyParts(value)
    const date = rawParts ? null : validDate(value)
    if (!rawParts && !date) return fallback
    try {
      const parts = rawParts || configuredDateParts(date!, localization.value.timezone)
      return formatPattern(parts, localization.value.dateFormat, localization.value.locale)
    }
    catch {
      return rawParts ? `${rawParts.year}-${rawParts.month}-${rawParts.day}` : String(value || fallback)
    }
  }

  function formatTime(value: unknown, fallback = '—') {
    const date = validDate(value)
    if (!date) return fallback
    const showSeconds = localization.value.timeFormat.includes('ss')
    const hour12 = localization.value.timeFormat.toLowerCase().includes('a')
    try {
      return new Intl.DateTimeFormat(localization.value.locale, {
        timeZone: localization.value.timezone,
        hour: hour12 ? 'numeric' : '2-digit',
        minute: '2-digit',
        ...(showSeconds ? { second: '2-digit' as const } : {}),
        hour12,
      }).format(date)
    }
    catch {
      return String(value || fallback)
    }
  }

  function formatDateTime(value: unknown, fallback = '—') {
    const date = validDate(value)
    if (!date) return fallback
    return `${formatDate(value, fallback)} ${formatTime(value, '')}`.trim()
  }

  function formatDatePart(
    value: unknown,
    options: Intl.DateTimeFormatOptions,
    fallback = '—',
  ) {
    const date = validDate(value)
    if (!date) return fallback
    try {
      return new Intl.DateTimeFormat(localization.value.locale, {
        ...options,
        timeZone: options.timeZone || localization.value.timezone,
      }).format(date)
    }
    catch {
      return String(value || fallback)
    }
  }

  function formatNumber(value: unknown, options: Intl.NumberFormatOptions = {}) {
    const number = Number(value)
    if (!Number.isFinite(number)) return String(value ?? '')
    try {
      const formatLocales: Record<string, string> = {
        '1,234.56': 'en-US',
        '1.234,56': 'de-DE',
        '1 234,56': 'fr-FR',
      }
      const numberLocale = formatLocales[localization.value.numberFormat] || localization.value.locale
      return new Intl.NumberFormat(numberLocale, options).format(number)
    }
    catch {
      return String(number)
    }
  }

  function formatCurrency(value: unknown, currency = localization.value.currency) {
    return formatNumber(value, { style: 'currency', currency })
  }

  onMounted(() => { void load() })

  return {
    localization: readonly(localization),
    loaded: readonly(loaded),
    loading: readonly(loading),
    load,
    apply,
    formatDate,
    formatTime,
    formatDateTime,
    formatDatePart,
    formatNumber,
    formatCurrency,
  }
}

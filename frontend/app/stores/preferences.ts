import { defineStore } from 'pinia'
import { computed } from 'vue'
import type { AppFontSize } from '~/types/docetra/settings'

const THEME_PRIMARY_KEY = 'ui:theme:primary'
const THEME_NEUTRAL_KEY = 'ui:theme:neutral'
const LOCALE_KEY = 'ui:locale'
const FONT_SIZE_KEY = 'ui:font-size'

export type AppLocale = 'en' | 'km'

type UiColorConfig = { primary?: string; neutral?: string }

const FONT_SIZE_PX: Record<AppFontSize, string> = {
  sm: '14px',
  md: '16px',
  lg: '18px',
  xl: '20px',
}

const DEFAULT_FONT_SIZE: AppFontSize = 'md'

function normalizeFontSize(value: string | null | undefined): AppFontSize {
  if (value === 'sm' || value === 'md' || value === 'lg' || value === 'xl') return value
  return DEFAULT_FONT_SIZE
}

/**
 * Cross-page UI preferences (theme colors, font size, locale).
 * Persists to localStorage; hydrates once per session via useState guards.
 */
export const usePreferencesStore = defineStore('preferences', () => {
  const appConfig = useAppConfig()
  const i18n = useI18n()

  const isThemeLoaded = useState('ui-theme-loaded', () => false)
  const isLocaleLoaded = useState('ui-locale-loaded', () => false)
  const isFontSizeLoaded = useState('ui-font-size-loaded', () => false)
  const fontSize = useState<AppFontSize>('ui-font-size', () => DEFAULT_FONT_SIZE)

  const uiColors = computed<UiColorConfig>(() =>
    ((appConfig.ui as { colors?: UiColorConfig }).colors ?? {}),
  )

  function setThemeColors(nextColors: UiColorConfig) {
    ;(appConfig.ui as { colors?: UiColorConfig }).colors = {
      ...(appConfig.ui as { colors?: UiColorConfig }).colors,
      ...nextColors,
    }
  }

  function loadThemeFromLocal() {
    if (typeof window === 'undefined') return
    const primary = localStorage.getItem(THEME_PRIMARY_KEY) || undefined
    const neutral = localStorage.getItem(THEME_NEUTRAL_KEY) || undefined
    if (!primary && !neutral) return
    setThemeColors({
      ...(primary ? { primary } : {}),
      ...(neutral ? { neutral } : {}),
    })
  }

  function persistThemeToLocal(nextColors: UiColorConfig) {
    if (typeof window === 'undefined') return
    if (nextColors.primary) localStorage.setItem(THEME_PRIMARY_KEY, nextColors.primary)
    if (nextColors.neutral) localStorage.setItem(THEME_NEUTRAL_KEY, nextColors.neutral)
  }

  function applyThemeColor(key: 'primary' | 'neutral', color: string) {
    const next = { [key]: color } as UiColorConfig
    setThemeColors(next)
    persistThemeToLocal(next)
  }

  function applyFontSizeToDom(size: AppFontSize) {
    if (!import.meta.client) return
    const px = FONT_SIZE_PX[size]
    const root = document.documentElement
    root.style.setProperty('--app-font-size', px)
    root.style.fontSize = px
  }

  function loadFontSizeFromLocal() {
    if (typeof window === 'undefined') return
    const saved = normalizeFontSize(localStorage.getItem(FONT_SIZE_KEY))
    fontSize.value = saved
    applyFontSizeToDom(saved)
  }

  function setFontSize(size: AppFontSize) {
    const next = normalizeFontSize(size)
    fontSize.value = next
    if (import.meta.client) localStorage.setItem(FONT_SIZE_KEY, next)
    applyFontSizeToDom(next)
  }

  function loadLocaleFromLocal() {
    if (typeof window === 'undefined') return
    const savedLocale = localStorage.getItem(LOCALE_KEY)
    if (savedLocale === 'en' || savedLocale === 'km') {
      void i18n.setLocale(savedLocale)
      return
    }
    localStorage.setItem(LOCALE_KEY, 'en')
    void i18n.setLocale('en')
  }

  function setLocale(code: AppLocale) {
    if (import.meta.client) localStorage.setItem(LOCALE_KEY, code)
    void i18n.setLocale(code)
  }

  function hydrate() {
    if (!import.meta.client) return
    if (!isThemeLoaded.value) {
      loadThemeFromLocal()
      isThemeLoaded.value = true
    }
    if (!isLocaleLoaded.value) {
      loadLocaleFromLocal()
      isLocaleLoaded.value = true
    }
    if (!isFontSizeLoaded.value) {
      loadFontSizeFromLocal()
      isFontSizeLoaded.value = true
    }
  }

  return {
    uiColors,
    fontSize,
    fontSizePx: FONT_SIZE_PX,
    hydrate,
    applyThemeColor,
    setLocale,
    setFontSize,
  }
})

import { defineStore } from 'pinia'
import { computed } from 'vue'

const THEME_PRIMARY_KEY = 'ui:theme:primary'
const THEME_NEUTRAL_KEY = 'ui:theme:neutral'
const LOCALE_KEY = 'ui:locale'

export type AppLocale = 'en' | 'km'

type UiColorConfig = { primary?: string; neutral?: string }

/**
 * Cross-page UI preferences (theme colors + locale).
 * Persists to localStorage; hydrates once per session via useState guards.
 */
export const usePreferencesStore = defineStore('preferences', () => {
  const appConfig = useAppConfig()
  const i18n = useI18n()

  const isThemeLoaded = useState('ui-theme-loaded', () => false)
  const isLocaleLoaded = useState('ui-locale-loaded', () => false)

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

  function loadLocaleFromLocal() {
    if (typeof window === 'undefined') return
    const savedLocale = localStorage.getItem(LOCALE_KEY)
    if (savedLocale === 'en' || savedLocale === 'km') {
      void i18n.setLocale(savedLocale)
    }
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
  }

  return {
    uiColors,
    hydrate,
    applyThemeColor,
    setLocale,
  }
})

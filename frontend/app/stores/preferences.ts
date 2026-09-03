import { defineStore } from 'pinia'
import { computed } from 'vue'
import type { AppFontSize } from '~/types/docetra/settings'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'
import { DEFAULT_FONT_SIZE, FONT_SIZE_PX, normalizeFontSize } from '~/utils/preferences/font-size'

const THEME_PRIMARY_KEY = 'ui:theme:primary'
const THEME_NEUTRAL_KEY = 'ui:theme:neutral'
const LOCALE_KEY = 'ui:locale'
const LOCALE_EXPLICIT_KEY = 'ui:locale:explicit'
const FONT_SIZE_KEY = 'ui:font-size'

export type AppLocale = 'en' | 'km'

type UiColorConfig = { primary?: string; neutral?: string }

/**
 * Cross-page UI preferences (theme colors, font size, locale).
 * Persists to localStorage; hydrates once per session via useState guards.
 */
export const usePreferencesStore = defineStore('preferences', () => {
  const appConfig = useAppConfig()
  const i18n = useI18n()
  // The app root controls when the remote config request starts. Local UI
  // preferences can paint immediately without waiting for the API.
  const appLocalization = useAppLocalization({ autoLoad: false })

  const isThemeLoaded = useState('ui-theme-loaded', () => false)
  const isLocaleLoaded = useState('ui-locale-loaded', () => false)
  const isFontSizeLoaded = useState('ui-font-size-loaded', () => false)
  const fontSize = useState<AppFontSize>('ui-font-size', () => DEFAULT_FONT_SIZE)
  const availableLocales = computed<AppLocale[]>(() => {
    const configured = appLocalization.localization.value.availableLanguages
      .filter((code): code is AppLocale => code === 'en' || code === 'km')
    return configured.length ? configured : ['en', 'km']
  })

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
    const isExplicit = localStorage.getItem(LOCALE_EXPLICIT_KEY) === '1'
    if (isExplicit && (savedLocale === 'en' || savedLocale === 'km')) {
      void i18n.setLocale(savedLocale)
    }
  }

  async function loadRemoteLocalization() {
    await appLocalization.load()
    const savedLocale = localStorage.getItem(LOCALE_KEY)
    const isExplicit = localStorage.getItem(LOCALE_EXPLICIT_KEY) === '1'
    if (isExplicit && (savedLocale === 'en' || savedLocale === 'km') && availableLocales.value.includes(savedLocale)) {
      void i18n.setLocale(savedLocale)
      return
    }
    const configured = appLocalization.localization.value.defaultLanguage
    void i18n.setLocale(configured === 'km' ? 'km' : 'en')
  }

  function setLocale(code: AppLocale) {
    const next = availableLocales.value.includes(code)
      ? code
      : (availableLocales.value.includes(appLocalization.localization.value.defaultLanguage)
          ? appLocalization.localization.value.defaultLanguage
          : availableLocales.value[0]!)
    if (import.meta.client) {
      localStorage.setItem(LOCALE_KEY, next)
      localStorage.setItem(LOCALE_EXPLICIT_KEY, '1')
    }
    void i18n.setLocale(next)
  }

  function syncLocaleWithConfig() {
    const current = i18n.locale.value as AppLocale
    if (availableLocales.value.includes(current)) return
    const next = availableLocales.value.includes(appLocalization.localization.value.defaultLanguage)
      ? appLocalization.localization.value.defaultLanguage
      : availableLocales.value[0]!
    if (import.meta.client) localStorage.removeItem(LOCALE_EXPLICIT_KEY)
    void i18n.setLocale(next)
  }

  function hydrateLocal() {
    if (!import.meta.client) return
    if (!isThemeLoaded.value) {
      loadThemeFromLocal()
      isThemeLoaded.value = true
    }
    if (!isFontSizeLoaded.value) {
      loadFontSizeFromLocal()
      isFontSizeLoaded.value = true
    }
    if (!isLocaleLoaded.value) {
      loadLocaleFromLocal()
      isLocaleLoaded.value = true
    }
  }

  async function hydrateRemote() {
    if (!import.meta.client) return
    await loadRemoteLocalization()
  }

  async function hydrate() {
    hydrateLocal()
    await hydrateRemote()
  }

  return {
    uiColors,
    fontSize,
    availableLocales,
    fontSizePx: FONT_SIZE_PX,
    hydrate,
    hydrateLocal,
    hydrateRemote,
    applyThemeColor,
    setLocale,
    syncLocaleWithConfig,
    setFontSize,
  }
})

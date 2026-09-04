<script setup lang="ts">
import { en, km } from '@nuxt/ui/locale'
import { createHttpAppInfoRepository } from '~/repositories/http/settings'
import { useAppBranding } from '~/composables/settings/useAppBranding'
import { usePreferencesStore } from '~/stores/preferences'

const colorMode = useColorMode()
const { locale, t } = useI18n()
const { applyFromAppInfo } = useAppBranding()
const preferences = usePreferencesStore()

const uiLocales: Record<string, typeof en> = { en, km }

const color = computed(() => colorMode.value === 'dark' ? '#1b1718' : 'white')
const currentLocale = computed(() => uiLocales[locale.value] || en)
const lang = computed(() => currentLocale.value.code || locale.value)
const dir = computed(() => currentLocale.value.dir || 'ltr')
const route = useRoute()
/** Remount on path change so list / create / detail do not reuse a stale page.
 *  Use `path` (not `fullPath`) so filter/sort/page query updates do not destroy the view. */
const pageKey = computed(() => route.path)

const siteName = computed(() => t('docetra.brand.name'))
const appDescription = computed(() => t('app.description'))
const appKeywords = computed(() => t('app.keywords'))
const { absoluteUrl, absolutePageUrl } = useSeoAbsoluteUrl()
const defaultOgImage = computed(() => absoluteUrl('/og-image.png'))
const pageUrl = computed(() => absolutePageUrl())
const remoteSettingsStarted = ref(false)

function loadRemoteSettings() {
  if (remoteSettingsStarted.value) return
  remoteSettingsStarted.value = true
  void preferences.hydrateRemote()
  void createHttpAppInfoRepository().get()
    .then(info => applyFromAppInfo(info))
    .catch(() => applyFromAppInfo(null))
}

function scheduleRemoteSettings(path = route.path) {
  if (remoteSettingsStarted.value || path.startsWith('/auth/')) return
  if ('requestIdleCallback' in window) {
    window.requestIdleCallback(loadRemoteSettings, { timeout: 2000 })
    return
  }
  globalThis.setTimeout(loadRemoteSettings, 0)
}

onMounted(() => {
  // Apply browser-owned preferences before the first interactive frame. They
  // must never wait behind a configuration request.
  preferences.hydrateLocal()
})

onNuxtReady(() => {
  // Remote localization and branding are enhancements. Nuxt schedules this
  // callback during browser idle time. Public auth routes use their safe local
  // defaults and avoid two unrelated API calls entirely.
  scheduleRemoteSettings()
})

watch(() => route.path, path => scheduleRemoteSettings(path))

useHead({
  // Page title only in the tab — do not append "Docetra" again.
  titleTemplate: (titleChunk) => {
    const chunk = titleChunk?.trim()
    if (!chunk || chunk === siteName.value) return siteName.value
    return chunk
  },
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { key: 'theme-color', name: 'theme-color', content: color },
    { key: 'keywords', name: 'keywords', content: appKeywords },
  ],
  link: [
    { rel: 'icon', type: 'image/png', href: '/logo.png' },
    { rel: 'apple-touch-icon', href: '/logo.png' },
  ],
  htmlAttrs: {
    lang,
    dir,
  },
})

useSeoMeta({
  description: appDescription,
  ogSiteName: siteName,
  ogTitle: siteName,
  ogDescription: appDescription,
  ogImage: () => defaultOgImage.value,
  ogImageAlt: siteName,
  ogUrl: () => pageUrl.value,
  ogType: 'website',
  twitterTitle: siteName,
  twitterDescription: appDescription,
  twitterImage: () => defaultOgImage.value,
  twitterImageAlt: siteName,
  twitterCard: 'summary_large_image',
  robots: 'noindex, nofollow',
})
</script>

<template>
  <UApp :locale="currentLocale">
    <NuxtLoadingIndicator
      color="var(--ui-primary, #e8472a)"
      error-color="#ef4444"
      :height="3"
    />
    <NuxtLayout>
      <NuxtPage :page-key="pageKey" />
    </NuxtLayout>
    <CommonAppConfirmHost />
  </UApp>
</template>

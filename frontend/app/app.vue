<script setup lang="ts">
import { en, km } from '@nuxt/ui/locale'
import { useSettingsRepositories } from '~/repositories'
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

const appDescription = computed(() => t('app.description'))

onMounted(() => {
  preferences.hydrate()
  // Non-blocking branding hydrate — do not stall first paint
  void useSettingsRepositories().appInfo.get()
    .then(info => applyFromAppInfo(info))
    .catch(() => applyFromAppInfo(null))
})

useHead({
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { key: 'theme-color', name: 'theme-color', content: color },
  ],
  link: [
    { rel: 'icon', type: 'image/png', href: '/logo.png' },
  ],
  htmlAttrs: {
    lang,
    dir,
  },
})

const title = 'Docetra'

useSeoMeta({
  title,
  description: appDescription,
  ogTitle: title,
  ogDescription: appDescription,
  ogImage: '/assets/images/logo.png',
  twitterImage: '/assets/images/logo.png',
  twitterCard: 'summary_large_image',
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
      <NuxtPage />
    </NuxtLayout>
    <CommonAppConfirmHost />
  </UApp>
</template>

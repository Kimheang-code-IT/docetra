<script setup lang="ts">
import * as locales from '@nuxt/ui/locale'

const colorMode = useColorMode()
const { locale } = useI18n()

const color = computed(() => colorMode.value === 'dark' ? '#1b1718' : 'white')
const lang = computed(() => locales[locale.value as keyof typeof locales]?.code || locale.value)
const dir = computed(() => locales[locale.value as keyof typeof locales]?.dir || 'ltr')

const currentLocale = computed(() => locales[locale.value as keyof typeof locales])

useHead({
  meta: [
    { charset: 'utf-8' },
    { name: 'viewport', content: 'width=device-width, initial-scale=1' },
    { key: 'theme-color', name: 'theme-color', content: color }
  ],
  link: [
    { rel: 'icon', type: 'image/png', href: '/logo.png' },
    { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
    { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
    { rel: 'stylesheet', href: 'https://fonts.googleapis.com/css2?family=Siemreap&family=Kantumruy+Pro:ital,wght@0,100..700;1,100..700&display=swap' }
  ],
  htmlAttrs: {
    lang,
    dir
  }
})

const title = 'Docetra'
const description = 'Centralized administrative record management for documents, meetings, organizations, and controlled access.'

useSeoMeta({
  title,
  description,
  ogTitle: title,
  ogDescription: description,
  ogImage: '/assets/images/logo.png',
  twitterImage: '/assets/images/logo.png',
  twitterCard: 'summary_large_image'
})
</script>

<template>
  <UApp :locale="currentLocale">
    <NuxtLoadingIndicator />
    <NuxtLayout>
      <NuxtPage />
    </NuxtLayout>
  </UApp>
</template>

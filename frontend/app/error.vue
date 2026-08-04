<script setup lang="ts">
import type { NuxtError } from '#app'

defineProps<{
  error: NuxtError
}>()

const { locale, t } = useI18n()
const title = computed(() => t('pages.error.title'))
const description = computed(() => t('pages.error.description'))

useSeoMeta({
  title,
  description
})

useHead({
  htmlAttrs: {
    lang: locale
  }
})
</script>

<template>
  <UApp>
    <UError :error="error" />
  </UApp>
</template>

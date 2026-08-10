type PageSeoOptions = {
  /** Browser tab / document title — page name only (no brand suffix). */
  title: MaybeRefOrGetter<string>
  description?: MaybeRefOrGetter<string | undefined | null>
  /** Default: noindex for authenticated app; auth pages should pass `index, follow`. */
  robots?: MaybeRefOrGetter<string | undefined>
  ogImage?: MaybeRefOrGetter<string | undefined>
}

/**
 * Per-page SEO. Titles are the page label only — brand is not appended
 * (see `titleTemplate` in `app.vue`).
 */
export function usePageSeo(options: PageSeoOptions) {
  const { t } = useI18n()

  const title = computed(() => {
    const value = toValue(options.title)?.trim()
    return value || t('docetra.brand.name')
  })

  const description = computed(() => {
    const value = toValue(options.description)?.trim()
    return value || t('app.description')
  })

  const robots = computed(() => toValue(options.robots) || 'noindex, nofollow')
  const ogImage = computed(() => toValue(options.ogImage) || '/logo.png')

  useHead(() => ({
    title: title.value,
  }))

  useSeoMeta({
    title: () => title.value,
    description: () => description.value,
    ogTitle: () => title.value,
    ogDescription: () => description.value,
    ogImage: () => ogImage.value,
    twitterTitle: () => title.value,
    twitterDescription: () => description.value,
    twitterImage: () => ogImage.value,
    twitterCard: 'summary',
    robots: () => robots.value,
  })
}

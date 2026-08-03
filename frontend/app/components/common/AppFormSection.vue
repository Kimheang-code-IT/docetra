<script setup lang="ts">
const props = withDefaults(defineProps<{
  title?: string
  titleKey?: string
  description?: string
  descriptionKey?: string
  columns?: 1 | 2
}>(), {
  columns: 2,
})

const { t, te } = useI18n()

const titleText = computed(() => {
  if (props.title) return props.title
  if (props.titleKey && te(props.titleKey)) return t(props.titleKey)
  return ''
})

const descriptionText = computed(() => {
  if (props.description) return props.description
  if (props.descriptionKey && te(props.descriptionKey)) return t(props.descriptionKey)
  return ''
})
</script>

<template>
  <section class="space-y-3">
    <header v-if="titleText || descriptionText" class="space-y-1">
      <h4 v-if="titleText" class="text-sm font-semibold text-highlighted">
        {{ titleText }}
      </h4>
      <p v-if="descriptionText" class="text-xs text-muted">
        {{ descriptionText }}
      </p>
    </header>
    <div
      class="grid gap-4"
      :class="columns === 2 ? 'md:grid-cols-2' : 'grid-cols-1'"
    >
      <slot />
    </div>
  </section>
</template>

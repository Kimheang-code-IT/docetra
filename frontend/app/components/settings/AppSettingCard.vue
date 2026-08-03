<script setup lang="ts">
const props = withDefaults(defineProps<{
  title?: string
  titleKey?: string
  description?: string
  descriptionKey?: string
  icon?: string
}>(), {})

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
  <UCard :ui="{ body: 'space-y-4', header: 'flex items-start gap-3' }">
    <template #header>
      <div v-if="icon" class="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
        <UIcon :name="icon" class="size-4.5" />
      </div>
      <div class="min-w-0 flex-1">
        <h3 class="text-sm font-semibold text-highlighted">
          {{ titleText }}
        </h3>
        <p v-if="descriptionText" class="mt-0.5 text-xs text-muted">
          {{ descriptionText }}
        </p>
      </div>
      <div v-if="$slots.actions" class="shrink-0">
        <slot name="actions" />
      </div>
    </template>

    <slot />

    <template v-if="$slots.footer" #footer>
      <slot name="footer" />
    </template>
  </UCard>
</template>

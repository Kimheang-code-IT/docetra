<script setup lang="ts">
const props = withDefaults(defineProps<{
  status: string
  activeValues?: string[]
}>(), {
  activeValues: () => ['active', 'enabled', 'connected'],
})

const { t, te } = useI18n()

const isActive = computed(() =>
  props.activeValues.map(v => v.toLowerCase()).includes(String(props.status).toLowerCase()),
)

const label = computed(() => {
  const key = `docetra.status.${props.status}`
  if (te(key)) return t(key)
  return props.status
})

const color = computed(() => {
  const s = props.status.toLowerCase()
  if (['active', 'enabled', 'connected', 'completed', 'success'].includes(s)) return 'success' as const
  if (['disabled', 'archived', 'inactive'].includes(s)) return 'neutral' as const
  if (['failed', 'error'].includes(s)) return 'error' as const
  if (['pending', 'testing', 'draft'].includes(s)) return 'warning' as const
  return isActive.value ? 'success' as const : 'neutral' as const
})
</script>

<template>
  <UBadge :color="color" variant="subtle" class="capitalize">
    {{ label }}
  </UBadge>
</template>

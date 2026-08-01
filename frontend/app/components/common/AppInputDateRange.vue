<script setup lang="ts">
/**
 * Compact start / end date pair for board toolbars (Topic, Record stages).
 */
const start = defineModel<string>('start', { default: '' })
const end = defineModel<string>('end', { default: '' })

const props = withDefaults(defineProps<{
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  disabled?: boolean
  class?: string
}>(), {
  size: 'sm',
})

const { t } = useI18n()

watch([start, end], ([from, to]) => {
  const a = String(from || '').slice(0, 10)
  const b = String(to || '').slice(0, 10)
  if (a && b && a > b) {
    end.value = a
  }
})
</script>

<template>
  <div
    class="flex flex-wrap items-center gap-1.5"
    :class="props.class"
  >
    <CommonAppInputDate
      v-model="start"
      :size="size"
      :disabled="disabled"
      class="w-36 sm:w-40"
      :aria-label="t('docetra.fields.startDate')"
    />
    <span class="text-xs text-muted" aria-hidden="true">–</span>
    <CommonAppInputDate
      v-model="end"
      :size="size"
      :disabled="disabled"
      class="w-36 sm:w-40"
      :aria-label="t('docetra.fields.endDate')"
    />
  </div>
</template>

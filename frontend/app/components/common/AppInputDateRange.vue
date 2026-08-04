<script setup lang="ts">
/**
 * Compact start / end date-time pair for board toolbars (Topic, Record stages).
 * Default granularity is minute so filters support date + time.
 */
const start = defineModel<string>('start', { default: '' })
const end = defineModel<string>('end', { default: '' })

const props = withDefaults(defineProps<{
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  disabled?: boolean
  granularity?: 'day' | 'hour' | 'minute' | 'second'
  class?: string
}>(), {
  size: 'sm',
  granularity: 'minute',
})

const { t } = useI18n()

const isDateTime = computed(() => props.granularity !== 'day')

function comparable(value: string) {
  const v = String(value || '').trim()
  if (!v) return ''
  if (v.includes('T')) return v.slice(0, 16)
  return `${v.slice(0, 10)}T00:00`
}

watch([start, end], ([from, to]) => {
  const a = comparable(String(from || ''))
  const b = comparable(String(to || ''))
  if (a && b && a > b) {
    end.value = start.value
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
      :granularity="granularity"
      :class="isDateTime ? 'w-44 sm:w-52' : 'w-36 sm:w-40'"
      :aria-label="t('docetra.fields.startDate')"
    />
    <span class="text-xs text-muted" aria-hidden="true">–</span>
    <CommonAppInputDate
      v-model="end"
      :size="size"
      :disabled="disabled"
      :granularity="granularity"
      :class="isDateTime ? 'w-44 sm:w-52' : 'w-36 sm:w-40'"
      :aria-label="t('docetra.fields.endDate')"
    />
  </div>
</template>

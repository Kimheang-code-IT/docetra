<script setup lang="ts">
/**
 * Single unified Date Range filter component for all pages and toolbars.
 * Uses AppInputDate directly for start & end date pickers.
 * Renders inline start/end date inputs on desktop, and a compact filter icon button with popover on mobile.
 */
const start = defineModel<string>('start', { default: '' })
const end = defineModel<string>('end', { default: '' })

const props = withDefaults(defineProps<{
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  disabled?: boolean
  granularity?: 'day' | 'hour' | 'minute' | 'second'
  label?: string
  placeholder?: string
  icon?: string
  class?: string
  /** Render the inputs directly, useful inside an existing filter popover. */
  inline?: boolean
}>(), {
  size: 'sm',
  granularity: 'minute',
  icon: 'i-lucide-filter',
})

const { t } = useI18n()

const isDateTime = computed(() => props.granularity !== 'day')

const hasActiveFilter = computed(() =>
  Boolean((start.value || '').trim() || (end.value || '').trim()),
)

const filterLabel = computed(() =>
  props.label || t('docetra.fields.meetingDate'),
)

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

function clearFilter() {
  start.value = ''
  end.value = ''
}
</script>

<template>
  <div class="inline-flex items-center gap-1.5" :class="props.class">
    <!-- Desktop inline filter -->
    <div
      class="shrink-0 items-center gap-1.5"
      :class="props.inline ? 'flex' : 'hidden xl:flex'"
    >
      <div class="flex flex-nowrap items-center gap-1.5">
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
      <UButton
        v-if="hasActiveFilter"
        icon="i-lucide-x"
        color="neutral"
        variant="ghost"
        size="xs"
        square
        :aria-label="t('docetra.common.clear')"
        :title="t('docetra.common.clear')"
        @click="clearFilter"
      />
    </div>

    <!-- Mobile popover filter icon button -->
    <UPopover v-if="!props.inline" class="shrink-0 xl:hidden">
      <div class="relative">
        <UButton
          :icon="icon"
          :color="hasActiveFilter ? 'primary' : 'neutral'"
          :variant="hasActiveFilter ? 'soft' : 'outline'"
          :size="size"
          square
          :aria-label="filterLabel"
          :title="filterLabel"
        />
        <span
          v-if="hasActiveFilter"
          class="absolute -top-1 -right-1 size-2 rounded-full bg-primary ring-2 ring-default"
        />
      </div>

      <template #content>
        <div class="flex max-w-[calc(100vw-2rem)] flex-col gap-2.5 p-3">
          <div class="flex items-center justify-between gap-2 border-b border-default pb-2">
            <span class="text-xs font-semibold text-highlighted">
              {{ filterLabel }}
            </span>
            <UButton
              v-if="hasActiveFilter"
              color="neutral"
              variant="ghost"
              size="xs"
              class="h-6 px-1.5 text-xs text-muted hover:text-highlighted"
              @click="clearFilter"
            >
              {{ t('docetra.common.clear') }}
            </UButton>
          </div>

          <div class="flex max-w-full flex-nowrap items-center gap-1.5 overflow-x-auto">
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
        </div>
      </template>
    </UPopover>
  </div>
</template>

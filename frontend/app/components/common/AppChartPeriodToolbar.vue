<script setup lang="ts">
import { getFilterSelectUi } from '~/utils/filter/select-ui'

const year = defineModel<string>('year', { default: 'this' })
const period = defineModel<string>('period', { default: 'monthly' })

const emit = defineEmits<{
  refresh: []
  download: []
}>()

const { t, locale } = useI18n()

const yearUi = computed(() => getFilterSelectUi(Boolean(year.value)))
const periodUi = computed(() => getFilterSelectUi(Boolean(period.value)))

const currentYear = new Date().getFullYear()

const yearItems = computed(() => [
  { label: t('docetra.dashboard.chartFilters.thisYear'), value: 'this' },
  { label: t('docetra.dashboard.chartFilters.lastYear'), value: 'last' },
  ...Array.from({ length: 5 }, (_, i) => {
    const y = currentYear - i
    return { label: String(y), value: String(y) }
  }),
])

const periodItems = computed(() => [
  { label: t('docetra.dashboard.chartFilters.monthly'), value: 'monthly', icon: 'i-lucide-calendar' },
  { label: t('docetra.dashboard.chartFilters.quarterly'), value: 'quarterly', icon: 'i-lucide-calendar-range' },
  { label: t('docetra.dashboard.chartFilters.weekly'), value: 'weekly', icon: 'i-lucide-calendar-days' },
  { label: t('docetra.dashboard.chartFilters.yearly'), value: 'yearly', icon: 'i-lucide-calendar-clock' },
])

const moreItems = computed(() => [[
  {
    label: t('docetra.actions.refresh'),
    icon: 'i-lucide-refresh-cw',
    onSelect: () => emit('refresh'),
  },
  {
    label: t('docetra.actions.downloadPng'),
    icon: 'i-lucide-download',
    onSelect: () => emit('download'),
  },
]])
</script>

<template>
  <div class="flex shrink-0 flex-wrap items-center justify-end gap-1.5" :lang="locale">
    <USelect
      v-model="year"
      :items="yearItems"
      value-key="value"
      size="sm"
      class="w-30"
      color="neutral"
      :aria-label="$t('docetra.dashboard.chartFilters.pickYear')"
      :ui="yearUi"
    />

    <USelect
      v-model="period"
      :items="periodItems"
      value-key="value"
      size="sm"
      class="w-34"
      color="neutral"
      :aria-label="$t('docetra.dashboard.chartFilters.pickPeriod')"
      :ui="periodUi"
    />

    <UDropdownMenu :items="moreItems" :content="{ align: 'end' }">
      <UButton
        icon="i-lucide-ellipsis"
        color="neutral"
        variant="soft"
        size="sm"
        square
        class="rounded-lg"
        :aria-label="$t('docetra.actions.more')"
      />
    </UDropdownMenu>
  </div>
</template>

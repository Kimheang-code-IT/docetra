<script setup lang="ts">
import type { FilterDef } from '~/types/docetra/common'

const props = defineProps<{
  search: string
  filters: FilterDef[]
  filterValues: Record<string, string>
  view: string
  views: Array<'table' | 'kanban' | 'hierarchy'>
  sort: string
}>()

const emit = defineEmits<{
  'update:search': [string]
  'update:view': [string]
  'update:sort': [string]
  setFilter: [key: string, value: string | string[] | undefined]
  clearFilters: []
}>()

const { t } = useI18n()

const searchModel = computed({
  get: () => props.search,
  set: (value: string) => emit('update:search', value),
})

const sortItems = computed(() => [
  { label: t('docetra.sort.updatedDesc'), value: '-updatedAt' },
  { label: t('docetra.sort.updatedAsc'), value: 'updatedAt' },
  { label: t('docetra.sort.nameAsc'), value: 'name' },
  { label: t('docetra.sort.titleAsc'), value: 'title' },
])

const sortModel = computed({
  get: () => props.sort,
  set: (value: string | number | boolean | null) => emit('update:sort', String(value || '-updatedAt')),
})

const selectFilters = computed(() =>
  props.filters.filter(f => f.type === 'select' || f.type === 'multiselect'),
)

const activeChips = computed(() => {
  const chips: Array<{ key: string, label: string }> = []
  for (const filter of selectFilters.value) {
    const raw = props.filterValues[filter.key]
    if (!raw) continue
    const values = raw.split(',').map(v => v.trim()).filter(Boolean)
    for (const value of values) {
      const option = filter.options?.find(o => o.value === value)
      chips.push({
        key: `${filter.key}:${value}`,
        label: `${t(filter.labelKey)}: ${option ? t(option.labelKey || option.label) : value}`,
      })
    }
  }
  return chips
})

const viewItems = computed(() =>
  props.views.map(v => ({
    label: t(`docetra.views.${v}`),
    value: v,
    icon: v === 'kanban' ? 'i-lucide-columns-3' : v === 'hierarchy' ? 'i-lucide-git-branch' : 'i-lucide-table',
  })),
)

function filterModelValue(filter: FilterDef): string | string[] | null {
  const raw = props.filterValues[filter.key]
  if (!raw) return null
  if (filter.type === 'multiselect') {
    const values = raw.split(',').map(v => v.trim()).filter(Boolean)
    return values.length ? values : null
  }
  return raw
}

function onFilterChange(filter: FilterDef, value: string | string[] | null) {
  if (value == null || value === '' || (Array.isArray(value) && !value.length)) {
    emit('setFilter', filter.key, undefined)
    return
  }
  emit('setFilter', filter.key, value)
}

function removeChip(chipKey: string) {
  const sep = chipKey.indexOf(':')
  const filterKey = sep >= 0 ? chipKey.slice(0, sep) : chipKey
  const value = sep >= 0 ? chipKey.slice(sep + 1) : ''
  if (!filterKey) return
  const filter = props.filters.find(f => f.key === filterKey)
  const raw = props.filterValues[filterKey]
  if (!filter || !raw || !value) {
    emit('setFilter', filterKey, undefined)
    return
  }
  if (filter.type !== 'multiselect') {
    emit('setFilter', filterKey, undefined)
    return
  }
  const next = raw.split(',').map(v => v.trim()).filter(v => v && v !== value)
  emit('setFilter', filterKey, next.length ? next : undefined)
}
</script>

<template>
  <div class="shrink-0 space-y-2 border-b border-default bg-default px-3 py-2.5">
    <div class="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
      <UInput
        v-model="searchModel"
        icon="i-lucide-search"
        :placeholder="$t('common.search')"
        size="md"
        class="w-full xl:max-w-[16rem]"
        :ui="{
          base: 'rounded-md bg-default ring-1 ring-default focus-visible:ring-2 focus-visible:ring-primary/30',
        }"
      />

      <div class="flex min-w-0 flex-1 flex-wrap items-center gap-2 xl:justify-end">
        <CommonAppFilterSelect
          v-for="filter in selectFilters"
          :key="filter.key"
          :filter="filter"
          :model-value="filterModelValue(filter)"
          @update:model-value="(v) => onFilterChange(filter, v)"
        />

        <CommonAppSingleFilterSelect
          v-model="sortModel"
          :items="sortItems"
          :label="$t('docetra.sort.updatedDesc')"
          :placeholder="$t('docetra.sort.updatedDesc')"
          icon="i-lucide-list-filter"
        />

        <UTabs
          v-if="views.length > 1"
          :model-value="view"
          :items="viewItems"
          :content="false"
          size="sm"
          class="shrink-0"
          @update:model-value="(v: string | number) => emit('update:view', String(v))"
        />
      </div>
    </div>

    <div v-if="activeChips.length" class="flex flex-wrap items-center gap-2">
      <UBadge
        v-for="chip in activeChips"
        :key="chip.key"
        color="neutral"
        variant="subtle"
        class="cursor-pointer"
        @click="removeChip(chip.key)"
      >
        {{ chip.label }}
        <UIcon name="i-lucide-x" class="ml-1 size-3" />
      </UBadge>
      <UButton size="xs" color="neutral" variant="link" @click="emit('clearFilters')">
        {{ $t('docetra.actions.clearFilters') }}
      </UButton>
    </div>
  </div>
</template>

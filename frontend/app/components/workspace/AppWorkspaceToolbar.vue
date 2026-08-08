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

const sortMenuItems = computed(() => [sortItems.value.map(item => ({
  label: item.label,
  icon: sortModel.value === item.value ? 'i-lucide-check' : undefined,
  onSelect: () => { sortModel.value = item.value },
}))])

const selectFilters = computed(() =>
  props.filters.filter(f => f.type === 'select' || f.type === 'multiselect'),
)

const dateFilters = computed(() =>
  props.filters.filter(f => f.type === 'daterange'),
)

const viewItems = computed(() =>
  props.views.map(v => ({
    label: t(`docetra.views.${v}`),
    value: v,
    icon: v === 'kanban' ? 'i-lucide-columns-3' : v === 'hierarchy' ? 'i-lucide-git-branch' : 'i-lucide-table',
  })),
)

function getDateStart(filter: FilterDef): string {
  const key = filter.startKey || 'startDate'
  return props.filterValues[key] || props.filterValues.startDate || props.filterValues[`${filter.key}Start`] || ''
}

function setDateStart(filter: FilterDef, val: string) {
  const key = filter.startKey || 'startDate'
  emit('setFilter', key, val || undefined)
}

function getDateEnd(filter: FilterDef): string {
  const key = filter.endKey || 'endDate'
  return props.filterValues[key] || props.filterValues.endDate || props.filterValues[`${filter.key}End`] || ''
}

function setDateEnd(filter: FilterDef, val: string) {
  const key = filter.endKey || 'endDate'
  emit('setFilter', key, val || undefined)
}

const hasActiveFilters = computed(() => {
  const hasSelect = selectFilters.value.some(filter => {
    const value = props.filterValues[filter.key]
    return Boolean(value && value.length)
  })
  const hasDate = dateFilters.value.some(filter => {
    const start = getDateStart(filter)
    const end = getDateEnd(filter)
    return Boolean(start || end)
  })
  return hasSelect || hasDate
})

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
</script>

<template>
  <div class="shrink-0 border-b border-default bg-default px-3 py-2.5">
    <div class="flex items-center gap-2 lg:justify-between">
      <CommonAppLiveSearch
        v-model="searchModel"
        :placeholder="$t('common.search')"
        size="md"
        class="min-w-0 w-full max-w-[18.75rem] flex-1 lg:flex-none"
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

      <UPopover class="ms-auto shrink-0 lg:hidden">
        <UButton
          icon="i-lucide-filter"
          :color="hasActiveFilters ? 'primary' : 'neutral'"
          :variant="hasActiveFilters ? 'soft' : 'outline'"
          size="sm"
          square
          :aria-label="$t('docetra.actions.filter')"
        />
        <template #content>
          <div class="flex w-[calc(100vw-2rem)] max-w-4xl flex-nowrap items-center gap-2 overflow-x-auto p-3">
            <CommonAppFilterSelect
              v-for="filter in selectFilters"
              :key="filter.key"
              :filter="filter"
              :model-value="filterModelValue(filter)"
              class="shrink-0"
              @update:model-value="(v) => onFilterChange(filter, v)"
            />
            <template v-for="filter in dateFilters" :key="filter.key">
              <div class="shrink-0">
                <CommonAppDateRangeFilter
                  :start="getDateStart(filter)"
                  :end="getDateEnd(filter)"
                  :label="t(filter.labelKey)"
                  size="sm"
                  inline
                  @update:start="(v) => setDateStart(filter, v)"
                  @update:end="(v) => setDateEnd(filter, v)"
                />
              </div>
            </template>
            <CommonAppSingleFilterSelect
              v-model="sortModel"
              :items="sortItems"
              :label="$t('docetra.sort.label')"
              :placeholder="$t('docetra.sort.label')"
              :searchable="false"
              class="shrink-0"
            />
          </div>
        </template>
      </UPopover>

      <div class="hidden min-w-0 flex-1 flex-nowrap items-center justify-end gap-2 overflow-x-auto lg:flex">
        <CommonAppFilterSelect
          v-for="filter in selectFilters"
          :key="filter.key"
          :filter="filter"
          :model-value="filterModelValue(filter)"
          @update:model-value="(v) => onFilterChange(filter, v)"
        />

        <template v-for="filter in dateFilters" :key="filter.key">
          <CommonAppDateRangeFilter
            :start="getDateStart(filter)"
            :end="getDateEnd(filter)"
            :label="t(filter.labelKey)"
            size="sm"
            @update:start="(v) => setDateStart(filter, v)"
            @update:end="(v) => setDateEnd(filter, v)"
          />
        </template>

        <UDropdownMenu :items="sortMenuItems" :content="{ align: 'end' }">
          <UButton
            icon="i-lucide-arrow-up-down"
            color="neutral"
            variant="outline"
            size="sm"
            square
            class="shrink-0"
            :aria-label="$t('docetra.sort.label')"
          />
        </UDropdownMenu>
      </div>

    </div>
  </div>
</template>

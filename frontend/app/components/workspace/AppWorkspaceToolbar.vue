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

const selectFilters = computed(() =>
  props.filters.filter(f => f.type === 'select' || f.type === 'multiselect'),
)

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
</script>

<template>
  <div class="shrink-0 border-b border-default bg-default px-3 py-2.5">
    <div class="flex flex-col gap-2 xl:flex-row xl:items-center xl:justify-between">
      <CommonAppLiveSearch
        v-model="searchModel"
        :placeholder="$t('common.search')"
        size="md"
        class="w-full xl:max-w-[16rem]"
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
          :searchable="false"
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
  </div>
</template>

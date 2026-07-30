<script setup lang="ts">
import type { FilterDef } from '~/types/docetra/common'

const ALL_VALUE = '__all__'

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
  setFilter: [key: string, value: string | undefined]
  clearFilters: []
}>()

const { t } = useI18n()
const searchModel = computed({
  get: () => props.search,
  set: (value: string) => emit('update:search', value),
})

const activeChips = computed(() =>
  props.filters
    .map((filter) => {
      const value = props.filterValues[filter.key]
      if (!value) return null
      const option = filter.options?.find(o => o.value === value)
      return {
        key: filter.key,
        label: `${t(filter.labelKey)}: ${option ? t(option.labelKey || option.label) : value}`,
      }
    })
    .filter(Boolean) as Array<{ key: string, label: string }>,
)

const viewItems = computed(() =>
  props.views.map(v => ({
    label: t(`docetra.views.${v}`),
    value: v,
    icon: v === 'kanban' ? 'i-lucide-columns-3' : v === 'hierarchy' ? 'i-lucide-git-branch' : 'i-lucide-table',
  })),
)

function filterItems(filter: FilterDef) {
  return [
    { label: t(filter.labelKey), value: ALL_VALUE },
    ...(filter.options || [])
      .filter(o => o.value !== '')
      .map(o => ({
        label: t(o.labelKey || o.label),
        value: o.value,
      })),
  ]
}

function filterModelValue(key: string) {
  return props.filterValues[key] || ALL_VALUE
}

function onFilterChange(key: string, value: string) {
  emit('setFilter', key, !value || value === ALL_VALUE ? undefined : value)
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
        <USelect
          v-for="filter in filters"
          :key="filter.key"
          :model-value="filterModelValue(filter.key)"
          :items="filterItems(filter)"
          value-key="value"
          size="md"
          icon="i-lucide-funnel"
          class="min-w-[9rem] flex-1 sm:flex-none sm:w-40"
          :ui="{
            base: 'rounded-md bg-default ring-1 ring-default',
            trailingIcon: 'text-muted',
          }"
          @update:model-value="(v: string) => onFilterChange(filter.key, v)"
        />

        <USelect
          :model-value="sort"
          :items="[
            { label: $t('docetra.sort.updatedDesc'), value: '-updatedAt' },
            { label: $t('docetra.sort.updatedAsc'), value: 'updatedAt' },
            { label: $t('docetra.sort.nameAsc'), value: 'name' },
            { label: $t('docetra.sort.titleAsc'), value: 'title' },
          ]"
          value-key="value"
          size="md"
          icon="i-lucide-list-filter"
          class="min-w-[10rem] flex-1 sm:flex-none sm:w-44"
          :ui="{ base: 'rounded-md bg-default ring-1 ring-default' }"
          @update:model-value="(v: string) => emit('update:sort', v)"
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
        @click="emit('setFilter', chip.key, undefined)"
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

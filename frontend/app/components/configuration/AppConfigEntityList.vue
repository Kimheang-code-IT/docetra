<script setup lang="ts">
import type { FilterDef, TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'

const props = withDefaults(defineProps<{
  titleKey: string
  descriptionKey?: string
  icon?: string
  canCreate?: boolean
  createLabelKey?: string
  columns: TableColumnDef[]
  rows: Record<string, unknown>[]
  total: number
  page: number
  limit: number
  pending?: boolean
  error?: string | null
  search: string
  sort?: string
  filters?: FilterDef[]
  filterValues?: Record<string, string>
  rowActions?: RowActionItem[]
  cellValue: (row: Record<string, unknown>, key: string) => string
}>(), {
  canCreate: true,
})

const emit = defineEmits<{
  create: []
  refresh: []
  'update:search': [string]
  'update:page': [number]
  'update:limit': [number]
  'update:selection': [string[]]
  'update:sort': [string]
  setFilter: [key: string, value: string | string[] | undefined]
  clearFilters: []
  rowClick: [Record<string, unknown>]
  rowAction: [payload: { key: string, row: Record<string, unknown> }]
  deleteSelected: [string[]]
  retry: []
}>()
</script>

<template>
  <WorkspaceAppWorkspacePage
    :title-key="props.titleKey"
    :description-key="props.descriptionKey"
    :icon="props.icon"
    :can-create="props.canCreate === true"
    :create-label-key="props.createLabelKey"
    @create="emit('create')"
    @refresh="emit('refresh')"
  >
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
      <WorkspaceAppWorkspaceToolbar
        :search="props.search"
        :filters="props.filters || []"
        :filter-values="props.filterValues || {}"
        view="table"
        :views="['table']"
        :sort="props.sort || '-updatedAt'"
        @update:search="emit('update:search', $event)"
        @update:sort="emit('update:sort', $event)"
        @set-filter="(key: string, value: string | string[] | undefined) => emit('setFilter', key, value)"
        @clear-filters="emit('clearFilters')"
      />

      <WorkspaceAppServerTable
        class="min-h-0 flex-1"
        :columns="props.columns"
        :rows="props.rows"
        :total="props.total"
        :page="props.page"
        :limit="props.limit"
        :pending="props.pending"
        :error="props.error"
        :cell-value="props.cellValue"
        :row-actions="props.rowActions"
        :show-meta="true"
        @update:page="emit('update:page', $event)"
        @update:limit="emit('update:limit', $event)"
        @update:selection="emit('update:selection', $event)"
        @row-click="emit('rowClick', $event)"
        @row-action="emit('rowAction', $event)"
        @delete-selected="emit('deleteSelected', $event)"
        @retry="emit('retry')"
      />
    </div>
  </WorkspaceAppWorkspacePage>
</template>

<script setup lang="ts">
import type { FilterDef, TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'

defineProps<{
  titleKey: string
  descriptionKey?: string
  icon?: string
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
}>()

const emit = defineEmits<{
  create: []
  refresh: []
  'update:search': [string]
  'update:page': [number]
  'update:limit': [number]
  'update:selection': [string[]]
  'update:sort': [string]
  setFilter: [key: string, value: string]
  clearFilters: []
  rowClick: [Record<string, unknown>]
  rowAction: [payload: { key: string, row: Record<string, unknown> }]
  deleteSelected: [string[]]
  retry: []
}>()
</script>

<template>
  <WorkspaceAppWorkspacePage
    :title-key="titleKey"
    :description-key="descriptionKey"
    :icon="icon"
    @create="emit('create')"
    @refresh="emit('refresh')"
  >
    <div class="flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
      <WorkspaceAppWorkspaceToolbar
        :search="search"
        :filters="filters || []"
        :filter-values="filterValues || {}"
        view="table"
        :views="['table']"
        :sort="sort || '-updatedAt'"
        @update:search="emit('update:search', $event)"
        @update:sort="emit('update:sort', $event)"
        @set-filter="(key: string, value: string | string[] | undefined) => emit('setFilter', key, Array.isArray(value) ? value[0] || '' : (value || ''))"
        @clear-filters="emit('clearFilters')"
      />

      <WorkspaceAppServerTable
        class="min-h-0 flex-1"
        :columns="columns"
        :rows="rows"
        :total="total"
        :page="page"
        :limit="limit"
        :pending="pending"
        :error="error"
        :cell-value="cellValue"
        :row-actions="rowActions"
        :show-meta="false"
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

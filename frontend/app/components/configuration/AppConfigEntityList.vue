<script setup lang="ts">
import type { FilterDef, TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'
import type { ExportRequest } from '~/types/docetra/export'

const props = withDefaults(defineProps<{
  titleKey: string
  descriptionKey?: string
  icon?: string
  canCreate?: boolean
  canDelete?: boolean
  canExport?: boolean
  createLabelKey?: string
  columns: TableColumnDef[]
  rows: Record<string, unknown>[]
  total: number
  page: number
  limit: number
  pending?: boolean
  error?: string | null
  exporting?: boolean
  search: string
  sort?: string
  filters?: FilterDef[]
  filterValues?: Record<string, string>
  rowActions?: RowActionItem[]
  showMeta?: boolean
  cellValue: (row: Record<string, unknown>, key: string) => string
}>(), {
  canCreate: true,
  canDelete: true,
  canExport: true,
  showMeta: true,
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
  export: [request: ExportRequest, selectedIds: string[]]
}>()

const { t } = useI18n()
const selectedIds = ref<string[]>([])
const exportFields = computed(() => props.columns
  .filter(() => props.canExport)
  .filter(column => column.key !== '_rowNumber' && column.key !== 'rowNumber')
  .map(column => ({ label: t(column.labelKey), value: column.key })))

function updateSelection(ids: string[]) {
  selectedIds.value = ids
  emit('update:selection', ids)
}
</script>

<template>
  <WorkspaceAppWorkspacePage
    :title-key="props.titleKey"
    :description-key="props.descriptionKey"
    :icon="props.icon"
    :can-create="props.canCreate === true"
    :create-label-key="props.createLabelKey"
    :refreshing="props.pending"
    :export-fields="props.canExport ? exportFields : []"
    :selected-count="selectedIds.length"
    :exporting="props.exporting"
    @create="emit('create')"
    @refresh="emit('refresh')"
    @export="emit('export', $event, selectedIds)"
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
        :can-delete="props.canDelete"
        :selectable="props.canDelete"
        :show-meta="props.showMeta"
        @update:page="emit('update:page', $event)"
        @update:limit="emit('update:limit', $event)"
        @update:selection="updateSelection"
        @row-click="emit('rowClick', $event)"
        @row-action="emit('rowAction', $event)"
        @delete-selected="emit('deleteSelected', $event)"
        @retry="emit('retry')"
      />
    </div>
  </WorkspaceAppWorkspacePage>
</template>

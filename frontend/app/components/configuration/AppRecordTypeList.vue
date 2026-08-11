<script setup lang="ts">
import { useConfigurationRepositories } from '~/repositories'
import { useConfigListPage } from '~/composables/configuration/useConfigListPage'
import type { FilterDef, TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'

const { recordTypes } = useConfigurationRepositories()
const { t } = useI18n()

const columns: TableColumnDef[] = [
  { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
  { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
  { key: 'icon', labelKey: 'docetra.common.icon' },
  { key: 'attributeCount', labelKey: 'docetra.fields.attributes' },
  { key: 'workflowEnabled', labelKey: 'docetra.fields.workflow' },
  { key: 'status', labelKey: 'docetra.fields.status', cell: 'badge' },
  { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', cell: 'datetime' },
]

const filters: FilterDef[] = [
  {
    key: 'status',
    labelKey: 'docetra.fields.status',
    type: 'multiselect',
    options: [
      { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
      { label: 'Disabled', value: 'disabled', labelKey: 'docetra.status.disabled' },
    ],
  },
  {
    key: 'workflowEnabled',
    labelKey: 'docetra.fields.workflow',
    type: 'multiselect',
    options: [
      { label: 'Yes', value: 'true', labelKey: 'docetra.common.yes' },
      { label: 'No', value: 'false', labelKey: 'docetra.common.no' },
    ],
  },
]

const list = useConfigListPage({
  titleKey: 'docetra.pages.recordType',
  descriptionKey: 'docetra.descriptions.recordType',
  icon: 'i-lucide-shapes',
  routeBase: '/configuration/record-types',
  exportResource: 'recordTypes',
  columns,
  async load(query) {
    const res = await recordTypes.list(query as any)
    return {
      data: (res.data || []).map(row => ({ ...row }) as Record<string, unknown>),
      total: res.meta?.total || 0,
    }
  },
  remove: id => recordTypes.remove(id),
  removeMany: ids => recordTypes.removeMany(ids),
  duplicate: id => recordTypes.duplicate(id).then(r => r as any),
  setActive: (id, active) => recordTypes.setActive(id, active).then(() => undefined),
  cellValue(row, key) {
    if (key === 'workflowEnabled') return row.workflowEnabled ? t('docetra.common.yes') : t('docetra.common.no')
    if (key === 'icon') return String(row.icon || '—')
    if (key === 'status') {
      const s = String(row.status || '')
      const i18nKey = `docetra.status.${s}`
      return t(i18nKey) !== i18nKey ? t(i18nKey) : s
    }
    if (key === 'updatedAt') return row.updatedAt ? new Date(String(row.updatedAt)).toLocaleString() : '—'
    return row[key] == null ? '—' : String(row[key])
  },
})

const searchInput = ref('')
const router = useRouter()
const rowActions = computed<RowActionItem[]>(() => [
  {
    key: 'assignFields',
    labelKey: 'docetra.rowActions.assignFields',
    icon: 'i-lucide-list-plus',
  },
  ...list.rowActions,
])

function onRowAction(payload: { key: string, row: Record<string, unknown> }) {
  if (payload.key === 'assignFields') {
    const id = String(payload.row.id || '')
    if (id) {
      void router.push({
        path: `/configuration/record-types/${id}`,
        query: { tab: 'attributes' },
      })
    }
    return
  }
  void list.onRowAction(payload)
}

watch(() => list.q, v => { searchInput.value = v })
</script>

<template>
  <ConfigurationAppConfigEntityList
    :title-key="list.titleKey"
    :description-key="list.descriptionKey"
    :icon="list.icon"
    create-label-key="docetra.config.createRecordType"
    :columns="list.columns"
    :rows="list.items"
    :total="list.total"
    :page="list.page"
    :limit="list.limit"
    :pending="list.pending"
    :error="list.error"
    :exporting="list.exporting"
    :search="searchInput"
    @export="list.exportData"
    :sort="list.sort"
    :filters="filters"
    :filter-values="list.filters"
    :row-actions="rowActions"
    :cell-value="list.defaultCellValue"
    @create="list.openCreate"
    @refresh="list.refresh"
    @update:search="(v) => { searchInput = v; list.debouncedSearch(v) }"
    @update:page="list.page = $event"
    @update:limit="list.limit = $event"
    @update:sort="list.sort = $event"
    @update:selection="list.selectedIds = $event"
    @set-filter="list.setFilter"
    @clear-filters="list.clearFilters"
    @row-click="list.openRow"
    @row-action="onRowAction"
    @delete-selected="list.requestDelete"
    @retry="list.refresh"
  />
</template>

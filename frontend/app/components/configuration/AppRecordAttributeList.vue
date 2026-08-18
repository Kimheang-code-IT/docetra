<script setup lang="ts">
import { useConfigurationRepositories } from '~/repositories'
import { useConfigListPage } from '~/composables/configuration/useConfigListPage'
import type { FilterDef, TableColumnDef } from '~/types/docetra/common'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

const { attributes } = useConfigurationRepositories()
const { t } = useI18n()
const { formatDateTime } = useAppLocalization()

const columns: TableColumnDef[] = [
  { key: '_rowNumber', labelKey: 'docetra.fields.number' },
  { key: 'label', labelKey: 'docetra.fields.name', sortable: true },
  { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
  { key: 'dataType', labelKey: 'docetra.config.dataTypeLabel' },
  { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', cell: 'datetime' },
  { key: 'updatedBy.name', labelKey: 'docetra.fields.updater', cell: 'person' },
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
    key: 'dataType',
    labelKey: 'docetra.config.dataTypeLabel',
    type: 'multiselect',
    options: [
      { label: 'Short text', value: 'short_text' },
      { label: 'Select', value: 'select' },
      { label: 'Date', value: 'date' },
      { label: 'Rich text', value: 'rich_text' },
      { label: 'Boolean', value: 'boolean' },
    ],
  },
  {
    key: 'unused',
    labelKey: 'docetra.config.usageFilter',
    type: 'select',
    options: [
      { label: 'All', value: '', labelKey: 'docetra.common.all' },
      { label: 'Unused only', value: 'true', labelKey: 'docetra.config.unusedOnly' },
    ],
  },
]

const list = useConfigListPage({
  titleKey: 'docetra.pages.recordAttribute',
  descriptionKey: 'docetra.descriptions.recordAttribute',
  icon: 'i-lucide-list-tree',
  routeBase: '/configuration/record-attributes',
  viewPermission: 'configuration.record_attributes.view',
  exportResource: 'recordAttributes',
  columns,
  async load(query) {
    const res = await attributes.list(query as any)
    const page = Number(query.page || 1)
    const limit = Number(query.limit || 20)
    return {
      data: (res.data || []).map((row, index) => ({
        ...row,
        _rowNumber: ((page - 1) * limit) + index + 1,
        updatedBy: row.updatedBy || {
          id: 'system',
          name: t('docetra.activity.system'),
        },
      }) as Record<string, unknown>),
      total: res.meta?.total || 0,
    }
  },
  remove: id => attributes.remove(id),
  removeMany: ids => attributes.removeMany(ids),
  duplicate: id => attributes.duplicate(id).then(r => r as any),
  setActive: (id, active) => attributes.setActive(id, active).then(() => undefined),
  cellValue(row, key) {
    if (key === 'dataType') {
      const dt = String(row.dataType || '')
      const i18nKey = `docetra.config.dataType.${dt}`
      return t(i18nKey) !== i18nKey ? t(i18nKey) : dt
    }
    if (key === 'updatedBy.name') {
      const updater = row.updatedBy as { name?: string } | undefined
      return updater?.name || t('docetra.activity.system')
    }
    if (key === 'updatedAt') {
      return formatDateTime(row.updatedAt)
    }
    return row[key] == null ? '—' : String(row[key])
  },
})

const searchInput = ref('')
watch(() => list.q, v => { searchInput.value = v })
</script>

<template>
  <ConfigurationAppConfigEntityList
    :title-key="list.titleKey"
    :description-key="list.descriptionKey"
    :icon="list.icon"
    create-label-key="docetra.config.createRecordAttribute"
    :can-create="list.canCreate"
    :can-delete="list.canDelete"
    :can-export="list.canExport"
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
    :row-actions="list.rowActions"
    :cell-value="list.defaultCellValue"
    :show-meta="true"
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
    @row-action="list.onRowAction"
    @delete-selected="list.requestDelete"
    @retry="list.refresh"
  />
</template>

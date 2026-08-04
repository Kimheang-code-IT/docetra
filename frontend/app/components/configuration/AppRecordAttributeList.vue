<script setup lang="ts">
import { useConfigurationRepositories } from '~/repositories'
import { useConfigListPage } from '~/composables/configuration/useConfigListPage'
import type { FilterDef, TableColumnDef } from '~/types/docetra/common'

const { attributes } = useConfigurationRepositories()
const { t } = useI18n()

const columns: TableColumnDef[] = [
  { key: 'label', labelKey: 'docetra.fields.label', sortable: true },
  { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
  { key: 'dataType', labelKey: 'docetra.config.dataTypeLabel' },
  { key: 'usedByCount', labelKey: 'docetra.fields.usage' },
  { key: 'required', labelKey: 'docetra.fields.required' },
  { key: 'searchable', labelKey: 'docetra.config.searchable' },
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
]

const list = useConfigListPage({
  titleKey: 'docetra.pages.recordAttribute',
  descriptionKey: 'docetra.descriptions.recordAttribute',
  icon: 'i-lucide-list-tree',
  routeBase: '/configuration/record-attributes',
  columns,
  async load(query) {
    const res = await attributes.list(query as any)
    return {
      data: (res.data || []).map(row => ({ ...row }) as Record<string, unknown>),
      total: res.meta?.total || 0,
    }
  },
  remove: id => attributes.remove(id),
  duplicate: id => attributes.duplicate(id).then(r => r as any),
  setActive: (id, active) => attributes.setActive(id, active).then(() => undefined),
  cellValue(row, key) {
    if (key === 'dataType') {
      const dt = String(row.dataType || '')
      const i18nKey = `docetra.config.dataType.${dt}`
      return t(i18nKey) !== i18nKey ? t(i18nKey) : dt
    }
    if (key === 'required' || key === 'searchable') {
      return row[key] ? t('docetra.common.yes') : t('docetra.common.no')
    }
    if (key === 'status') {
      const s = String(row.status || '')
      const i18nKey = `docetra.status.${s}`
      return t(i18nKey) !== i18nKey ? t(i18nKey) : s
    }
    if (key === 'updatedAt') {
      return row.updatedAt ? new Date(String(row.updatedAt)).toLocaleString() : '—'
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
    :columns="list.columns"
    :rows="list.items"
    :total="list.total"
    :page="list.page"
    :limit="list.limit"
    :pending="list.pending"
    :error="list.error"
    :search="searchInput"
    :sort="list.sort"
    :filters="filters"
    :filter-values="list.filters"
    :row-actions="list.rowActions"
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
    @row-action="list.onRowAction"
    @delete-selected="list.requestDelete"
    @retry="list.refresh"
  />
</template>

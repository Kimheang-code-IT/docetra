<script setup lang="ts">
import { useConfigurationRepositories } from '~/repositories'
import { useConfigListPage } from '~/composables/configuration/useConfigListPage'
import type { FilterDef, TableColumnDef } from '~/types/docetra/common'

const { documentTypes } = useConfigurationRepositories()
const { t } = useI18n()

const columns: TableColumnDef[] = [
  { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
  { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
  { key: 'direction', labelKey: 'docetra.config.direction' },
  { key: 'relatedRecordTypeName', labelKey: 'docetra.config.relatedRecordType' },
  { key: 'defaultPriority', labelKey: 'docetra.config.defaultPriority' },
  { key: 'status', labelKey: 'docetra.fields.status', cell: 'badge' },
  { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', cell: 'datetime' },
]

const filters: FilterDef[] = [
  {
    key: 'status',
    labelKey: 'docetra.fields.status',
    type: 'select',
    options: [
      { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
      { label: 'Disabled', value: 'disabled', labelKey: 'docetra.status.disabled' },
    ],
  },
  {
    key: 'direction',
    labelKey: 'docetra.config.direction',
    type: 'select',
    options: [
      { label: 'Incoming', value: 'incoming' },
      { label: 'Outgoing', value: 'outgoing' },
      { label: 'Internal', value: 'internal' },
      { label: 'Both', value: 'both' },
    ],
  },
]

const list = useConfigListPage({
  titleKey: 'docetra.pages.documentType',
  descriptionKey: 'docetra.descriptions.documentType',
  icon: 'i-lucide-files',
  routeBase: '/configuration/document-types',
  columns,
  async load(query) {
    const res = await documentTypes.list(query as any)
    return {
      data: (res.data || []).map(row => ({ ...row }) as Record<string, unknown>),
      total: res.meta?.total || 0,
    }
  },
  remove: id => documentTypes.remove(id),
  duplicate: id => documentTypes.duplicate(id).then(r => r as any),
  setActive: (id, active) => documentTypes.setActive(id, active).then(() => undefined),
})

const searchInput = ref('')
watch(() => list.q, v => { searchInput.value = v })
</script>

<template>
  <ConfigurationAppConfigEntityList
    :title-key="list.titleKey"
    :description-key="list.descriptionKey"
    :icon="list.icon"
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
  <CommonAppConfirmDialog
    v-model:open="list.confirmOpen"
    :title="t('docetra.common.confirmTitle')"
    :description="t('docetra.actions.deleteConfirm', { n: 1 })"
    :loading="list.deleting"
    @confirm="list.confirmDelete"
  />
</template>

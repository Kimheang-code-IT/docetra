<script setup lang="ts">
import type { EntityApiKey } from '~/composables/api/useEntityApis'
import type { FilterDef } from '~/types/docetra/common'
import {
  ARCHIVE_COLUMNS,
  useArchiveWorkspace,
} from '~/composables/archive/useArchiveWorkspace'

const {
  rowActions,
  canDeleteAny,
  canDeleteRow,
  sourceOptions,
  search,
  sourceFilter,
  dateStart,
  dateEnd,
  page,
  limit,
  visibleRows,
  filteredRows,
  pending,
  error,
  refresh,
  openRow,
  onRowAction,
  onDeleteSelected,
  cellValue,
  onLimitChange,
} = useArchiveWorkspace()

const archiveFilters = computed<FilterDef[]>(() => [
  { key: 'source', labelKey: 'docetra.archive.type', type: 'select', options: sourceOptions.value },
  { key: 'archivedAt', labelKey: 'docetra.archive.archivedAt', type: 'daterange', startKey: 'archivedAtStart', endKey: 'archivedAtEnd' },
])

const archiveFilterValues = computed<Record<string, string>>(() => ({
  source: sourceFilter.value === 'all' ? '' : sourceFilter.value,
  archivedAtStart: dateStart.value,
  archivedAtEnd: dateEnd.value,
}))

function onSetFilter(key: string, value: string | string[] | undefined) {
  if (key === 'source') {
    sourceFilter.value = (String(Array.isArray(value) ? value[0] : value) || 'all') as EntityApiKey | 'all'
    return
  }
  if (key === 'archivedAtStart') dateStart.value = value ? String(value) : ''
  if (key === 'archivedAtEnd') dateEnd.value = value ? String(value) : ''
}
</script>

<template>
  <WorkspaceAppWorkspacePage
    title-key="docetra.pages.archive"
    description-key="docetra.archive.description"
    icon="i-lucide-archive"
    :can-create="false"
    :refreshing="pending"
    @refresh="refresh"
  >
    <div class="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default shadow-xs">
      <WorkspaceAppServerTable
        :columns="ARCHIVE_COLUMNS"
        :rows="visibleRows"
        :total="filteredRows.length"
        :page="page"
        :limit="limit"
        :pending="pending"
        :error="error"
        :cell-value="cellValue"
        :can-delete="canDeleteAny"
        :selectable="canDeleteAny"
        :can-select-row="canDeleteRow"
        :show-meta="false"
        :row-actions="rowActions"
        @update:page="page = $event"
        @update:limit="onLimitChange"
        @row-click="openRow($event as any)"
        @row-action="onRowAction"
        @delete-selected="onDeleteSelected"
        @retry="refresh"
      >
        <template #toolbar>
          <WorkspaceAppWorkspaceToolbar
            v-model:search="search"
            :search-placeholder="$t('docetra.archive.searchPlaceholder')"
            :filters="archiveFilters"
            :filter-values="archiveFilterValues"
            @set-filter="onSetFilter"
          />
        </template>
      </WorkspaceAppServerTable>
    </div>
  </WorkspaceAppWorkspacePage>
</template>


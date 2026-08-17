<script setup lang="ts">
import {
  ARCHIVE_COLUMNS,
  useArchiveWorkspace,
} from '~/composables/archive/useArchiveWorkspace'

const {
  rowActions,
  sourceOptions,
  search,
  sourceFilter,
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
        :can-delete="true"
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
          <div class="flex shrink-0 flex-wrap items-center gap-2 border-b border-default bg-default px-3 py-2.5">
            <CommonAppLiveSearch
              v-model="search"
              :placeholder="$t('docetra.archive.searchPlaceholder')"
              size="md"
              class="min-w-0 w-full max-w-75 flex-1"
            />
            <USelect
              v-model="sourceFilter"
              :items="sourceOptions"
              value-key="value"
              size="sm"
              class="w-52"
              :aria-label="$t('docetra.archive.type')"
            />
            <div class="ms-auto flex items-center gap-2 text-sm text-muted">
              <UIcon name="i-lucide-archive" class="size-4" />
              <span>{{ $t('docetra.archive.itemCount', { n: filteredRows.length }) }}</span>
            </div>
          </div>
        </template>
      </WorkspaceAppServerTable>
    </div>
  </WorkspaceAppWorkspacePage>
</template>

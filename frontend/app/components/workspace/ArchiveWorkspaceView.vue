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

const hasArchiveFilters = computed(() =>
  sourceFilter.value !== 'all'
  || Boolean(dateStart.value.trim() || dateEnd.value.trim()),
)
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
          <div class="flex shrink-0 items-center gap-2 border-b border-default bg-default px-3 py-2.5 lg:justify-between">
            <CommonAppLiveSearch
              v-model="search"
              :placeholder="$t('docetra.archive.searchPlaceholder')"
              size="md"
              class="min-w-0 w-full max-w-[18.75rem] flex-1 lg:flex-none"
            />

            <UPopover class="ms-auto shrink-0 lg:hidden">
              <UButton
                icon="i-lucide-filter"
                :color="hasArchiveFilters ? 'primary' : 'neutral'"
                :variant="hasArchiveFilters ? 'soft' : 'outline'"
                size="sm"
                square
                :aria-label="$t('docetra.actions.filter')"
              />
              <template #content>
                <div class="flex w-[calc(100vw-2rem)] max-w-4xl flex-nowrap items-center gap-2 overflow-x-auto p-3">
                  <CommonAppSingleFilterSelect
                    v-model="sourceFilter"
                    :items="sourceOptions"
                    :label="$t('docetra.archive.type')"
                    :placeholder="$t('docetra.archive.allTypes')"
                    :searchable="false"
                    class="shrink-0"
                  />
                  <CommonAppDateRangeFilter
                    v-model:start="dateStart"
                    v-model:end="dateEnd"
                    :label="$t('docetra.archive.archivedAt')"
                    size="sm"
                    inline
                    class="shrink-0"
                  />
                </div>
              </template>
            </UPopover>

            <div class="hidden ms-auto shrink-0 flex-nowrap items-center gap-2 lg:flex">
              <CommonAppSingleFilterSelect
                v-model="sourceFilter"
                :items="sourceOptions"
                :label="$t('docetra.archive.type')"
                :placeholder="$t('docetra.archive.allTypes')"
                :searchable="false"
              />
              <CommonAppDateRangeFilter
                v-model:start="dateStart"
                v-model:end="dateEnd"
                :label="$t('docetra.archive.archivedAt')"
                size="sm"
              />
            </div>
          </div>
        </template>
      </WorkspaceAppServerTable>
    </div>
  </WorkspaceAppWorkspacePage>
</template>

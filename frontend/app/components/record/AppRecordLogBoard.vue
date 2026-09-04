<script setup lang="ts">
import { useRecordLogBoard } from '~/composables/record/useRecordLogBoard'
import { useAppLocalization } from '~/composables/settings/useAppLocalization'

const {
  pending,
  error,
  search,
  dateStart,
  dateEnd,
  tabs,
  selectedTabId,
  tabCounts,
  hasMoreRecordTypes,
  loadingMoreRecordTypes,
  loadMoreRecordTypes,
  page,
  limit,
  total,
  pageItems,
  columns,
  cellValue,
  selectTab,
  openRow,
  refresh,
} = useRecordLogBoard()

const leftCollapsed = useState('record-log-left-collapsed', () => false)
const { formatDateTime } = useAppLocalization()
const { t, te } = useI18n()

function tabLabel(tab: { label?: string, labelKey: string }) {
  return tab.label || t(tab.labelKey)
}

function tabDescription(tab: { description?: string, descriptionKey?: string }) {
  if (tab.description) return tab.description
  if (tab.descriptionKey && te(tab.descriptionKey)) return t(tab.descriptionKey)
  return ''
}

function logActionLabel(action: unknown) {
  const text = String(action || '')
  if (!text) return '—'
  const actionKey = `docetra.logActions.${text}`
  return te(actionKey) ? t(actionKey) : text.replaceAll('_', ' ')
}

function logActorName(row: Record<string, unknown>) {
  const actor = row.actor
  if (actor && typeof actor === 'object' && 'name' in actor) {
    return String((actor as { name?: string }).name || '—')
  }
  return '—'
}
</script>

<template>
  <WorkspaceAppWorkspaceBoardPage
    v-model:collapsed="leftCollapsed"
    v-model:header-search="search"
    v-model:date-start="dateStart"
    v-model:date-end="dateEnd"
    title-key="docetra.pages.recordLog"
    description-key="docetra.descriptions.recordLog"
    icon="i-lucide-scroll-text"
    rail-title-key="docetra.recordLogBoard.tabsTitle"
    rail-icon="i-lucide-scroll-text"
    expand-label-key="docetra.recordLogBoard.expandTabs"
    collapse-label-key="docetra.recordLogBoard.collapseTabs"
    header-search-placeholder-key="docetra.recordLogBoard.search"
    :pending="pending"
    :show-pending-overlay="pending && !pageItems.length && !tabCounts.get('all')"
    :error="error"
    @refresh="refresh"
    @retry="refresh"
  >
    <template #rail-items="{ railCollapsed, onRailSelect }">
      <WorkspaceAppBoardRailItem
        v-for="tab in tabs"
        :key="tab.id"
        :title="tabLabel(tab)"
        :count="tabCounts.get(tab.id) || 0"
        :icon="tab.icon"
        :selected="selectedTabId === tab.id"
        :collapsed="railCollapsed"
        count-style="badge"
        @select="onRailSelect(() => selectTab(tab.id))"
      >
        <template v-if="tabDescription(tab)" #subtitle>
          <p class="mt-1 line-clamp-2 text-xs app-card-text">
            {{ tabDescription(tab) }}
          </p>
        </template>
      </WorkspaceAppBoardRailItem>

      <UButton
        v-if="hasMoreRecordTypes && !railCollapsed"
        block
        color="neutral"
        variant="soft"
        icon="i-lucide-chevrons-down"
        :loading="loadingMoreRecordTypes"
        @click="loadMoreRecordTypes"
      >
        {{ $t('docetra.actions.loadMore') }}
      </UButton>
    </template>

    <WorkspaceAppBoardContent
      view-mode="table"
      :pending="pending"
      :empty="!pageItems.length"
      empty-icon="i-lucide-scroll-text"
      empty-label-key="docetra.states.empty"
      :columns="columns"
      :rows="pageItems as unknown as Record<string, unknown>[]"
      :total="total"
      :page="page"
      :limit="limit"
      :cell-value="cellValue"
      :selectable="false"
      :can-delete="false"
      :show-meta="true"
      :table-error="error"
      :row-actions="[
        { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
        { key: 'logs', labelKey: 'docetra.rowActions.logs', icon: 'i-lucide-scroll-text' },
      ]"
      @update:page="page = $event"
      @update:limit="limit = $event"
      @row-click="openRow"
      @row-action="({ key, row }) => key === 'detail' || key === 'logs' ? openRow(row) : undefined"
      @retry="refresh"
    >
      <article
        v-for="row in pageItems"
        :key="String(row.id)"
        role="button"
        tabindex="0"
        class="cursor-pointer rounded-lg border border-default bg-default p-3 text-left transition hover:border-primary/35"
        @click="openRow(row as unknown as Record<string, unknown>)"
        @keydown.enter.prevent="openRow(row as unknown as Record<string, unknown>)"
      >
        <div class="flex items-start gap-2">
          <div class="min-w-0 flex-1">
            <h3 class="truncate text-sm font-semibold text-highlighted">
              {{ row.entityTitle || row.summary || '—' }}
            </h3>
            <p class="mt-1 truncate text-xs text-muted">
              {{ logActionLabel(row.action) }}
              ·
              {{ row.recordTypeName || row.entityType || '—' }}
            </p>
          </div>
          <span class="app-card-field-highlight app-card-field-highlight--info shrink-0 text-xs">
            {{ formatDateTime(String(row.occurredAt || row.updatedAt || '')) || '—' }}
          </span>
        </div>
        <p class="mt-2 truncate text-xs app-card-text">
          {{ logActorName(row as unknown as Record<string, unknown>) }}
        </p>
      </article>
    </WorkspaceAppBoardContent>
  </WorkspaceAppWorkspaceBoardPage>
</template>

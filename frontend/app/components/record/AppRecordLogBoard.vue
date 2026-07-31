<script setup lang="ts">
import { useRecordLogBoard } from '~/composables/record/useRecordLogBoard'

const {
  pending,
  error,
  search,
  dateFilter,
  tabs,
  selectedTabId,
  selectedTab,
  tabCounts,
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

function toggleLeftPanel() {
  leftCollapsed.value = !leftCollapsed.value
}

onMounted(() => {
  refresh()
})
</script>

<template>
  <WorkspaceAppWorkspacePage
    title-key="docetra.pages.recordLog"
    description-key="docetra.descriptions.recordLog"
    icon="i-lucide-scroll-text"
    :can-create="false"
    @refresh="refresh"
  >
    <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
      <div
        v-if="pending && !pageItems.length && !tabCounts.get('all')"
        class="absolute inset-0 z-10 flex items-center justify-center bg-default/50"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <UAlert
        v-if="error"
        class="m-3"
        color="error"
        :title="error"
        :actions="[{ label: $t('docetra.actions.retry'), onClick: refresh }]"
      />

      <!-- Always left rail + right table (never stacked) -->
      <div class="flex min-h-0 flex-1 flex-row overflow-hidden">
        <!-- Left 1-col tab rail -->
        <aside
          class="flex h-full min-h-0 shrink-0 flex-col overflow-hidden border-e border-default bg-default transition-[width] duration-200"
          :style="{ width: leftCollapsed ? '3.5rem' : '16rem' }"
        >
          <div
            class="flex shrink-0 items-center border-b border-default"
            :class="leftCollapsed ? 'justify-center px-1.5 py-3.5' : 'px-4 py-3.5'"
          >
            <h2
              v-if="!leftCollapsed"
              class="truncate text-sm font-semibold text-highlighted"
            >
              {{ $t('docetra.recordLogBoard.tabsTitle') }}
            </h2>
            <UIcon
              v-else
              name="i-lucide-scroll-text"
              class="size-4 text-muted"
              :aria-label="$t('docetra.recordLogBoard.tabsTitle')"
            />
          </div>

          <nav
            class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden"
            :class="leftCollapsed ? 'space-y-1 p-1.5' : 'space-y-1.5 p-3'"
            :aria-label="$t('docetra.recordLogBoard.tabsTitle')"
          >
            <UTooltip
              v-for="tab in tabs"
              :key="tab.id"
              :text="$t(tab.labelKey)"
              :disabled="!leftCollapsed"
              :content="{ side: 'right', sideOffset: 8 }"
            >
              <button
                type="button"
                class="flex w-full items-center transition"
                :class="[
                  leftCollapsed
                    ? 'justify-center rounded-md p-2'
                    : 'gap-2 rounded-lg border px-2.5 py-2 text-left',
                  selectedTabId === tab.id
                    ? (leftCollapsed
                        ? 'bg-primary/10 text-primary ring-1 ring-primary/30'
                        : 'border-primary bg-primary/5 ring-1 ring-primary/25')
                    : (leftCollapsed
                        ? 'text-muted hover:bg-elevated hover:text-highlighted'
                        : 'border-default hover:border-primary/30'),
                ]"
                :aria-label="$t(tab.labelKey)"
                :aria-current="selectedTabId === tab.id ? 'page' : undefined"
                @click="selectTab(tab.id)"
              >
                <UIcon
                  :name="tab.icon"
                  class="size-4 shrink-0"
                  :class="selectedTabId === tab.id ? 'text-primary' : (leftCollapsed ? '' : 'text-muted')"
                />

                <template v-if="!leftCollapsed">
                  <span
                    class="min-w-0 flex-1 truncate text-sm"
                    :class="selectedTabId === tab.id ? 'font-semibold text-highlighted' : 'font-medium text-toned'"
                  >
                    {{ $t(tab.labelKey) }}
                  </span>
                  <UBadge
                    color="neutral"
                    variant="subtle"
                    size="sm"
                    class="shrink-0 tabular-nums"
                  >
                    {{ tabCounts.get(tab.id) || 0 }}
                  </UBadge>
                </template>
              </button>
            </UTooltip>
          </nav>
        </aside>

        <!-- Right table area -->
        <section class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
          <div class="flex shrink-0 items-center gap-3 border-b border-default px-4 py-3.5">
            <div class="flex min-w-0 flex-1 items-center gap-1.5">
              <UButton
                :icon="leftCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                :aria-label="leftCollapsed
                  ? $t('docetra.recordLogBoard.expandTabs')
                  : $t('docetra.recordLogBoard.collapseTabs')"
                :aria-expanded="!leftCollapsed"
                @click="toggleLeftPanel"
              />
              <h2 class="min-w-0 truncate text-sm font-semibold text-highlighted">
                {{ $t(selectedTab.labelKey) }}
              </h2>
            </div>

            <div class="flex shrink-0 items-center gap-2.5">
              <CommonAppInputDate
                v-model="dateFilter"
                size="sm"
                class="w-40"
              />
              <UInput
                v-model="search"
                icon="i-lucide-search"
                size="sm"
                class="w-48 lg:w-56"
                :placeholder="$t('docetra.recordLogBoard.search')"
              />
            </div>
          </div>

          <WorkspaceAppServerTable
            class="min-h-0 flex-1"
            :columns="columns"
            :rows="pageItems as any"
            :total="total"
            :page="page"
            :limit="limit"
            :pending="pending"
            :error="error"
            :cell-value="cellValue"
            :can-delete="false"
            :selectable="false"
            :show-meta="false"
            @update:page="page = $event"
            @update:limit="limit = $event"
            @row-click="openRow"
            @retry="refresh"
          />
        </section>
      </div>
    </div>
  </WorkspaceAppWorkspacePage>
</template>

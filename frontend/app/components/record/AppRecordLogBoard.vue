<script setup lang="ts">
import { useRecordLogBoard } from '~/composables/record/useRecordLogBoard'

const {
  pending,
  error,
  search,
  dateStart,
  dateEnd,
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
const mobileLogListOpen = ref(false)
const hasLogFilters = computed(() => Boolean(
  search.value.trim() || dateStart.value.trim() || dateEnd.value.trim(),
))

function toggleLeftPanel() {
  leftCollapsed.value = !leftCollapsed.value
}

function selectLogTab(id: string) {
  selectTab(id)
  mobileLogListOpen.value = false
}

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
      <div class="relative flex min-h-0 flex-1 flex-row overflow-hidden">
        <button
          v-if="mobileLogListOpen"
          type="button"
          class="absolute inset-0 z-20 bg-black/25 lg:hidden"
          :aria-label="$t('actions.close')"
          @click="mobileLogListOpen = false"
        />

        <!-- Left 1-col tab rail -->
        <aside
          class="flex h-full min-h-0 shrink-0 flex-col overflow-hidden border-e border-default bg-default transition-[width] duration-200 lg:static lg:z-auto lg:shadow-none"
          :class="[
            mobileLogListOpen
              ? 'absolute inset-y-0 start-0 z-30 w-[min(22rem,calc(100%-3rem))] shadow-xl'
              : 'relative w-14',
            leftCollapsed ? 'lg:w-14' : 'lg:w-[22rem]',
          ]"
        >
          <div
            class="flex shrink-0 items-center border-b border-default"
            :class="mobileLogListOpen
              ? 'justify-between px-4 py-3.5'
              : leftCollapsed
              ? 'justify-center px-1.5 py-3.5'
              : 'justify-center px-1.5 py-3.5 lg:justify-start lg:px-4'"
          >
            <h2
              v-if="mobileLogListOpen || !leftCollapsed"
              class="truncate text-sm font-semibold text-highlighted"
              :class="mobileLogListOpen ? '' : 'hidden lg:block'"
            >
              {{ $t('docetra.recordLogBoard.tabsTitle') }}
            </h2>
            <UIcon
              v-if="leftCollapsed && !mobileLogListOpen"
              name="i-lucide-scroll-text"
              class="size-4 text-muted"
              :aria-label="$t('docetra.recordLogBoard.tabsTitle')"
            />
            <UIcon
              v-else-if="!mobileLogListOpen"
              name="i-lucide-scroll-text"
              class="size-4 text-muted lg:hidden"
              :aria-label="$t('docetra.recordLogBoard.tabsTitle')"
            />
            <UButton
              v-if="mobileLogListOpen"
              icon="i-lucide-x"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="lg:hidden"
              :aria-label="$t('actions.close')"
              @click="mobileLogListOpen = false"
            />
          </div>

          <nav
            class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden"
            :class="mobileLogListOpen
              ? 'space-y-1.5 p-3'
              : leftCollapsed
                ? 'space-y-1 p-1.5'
                : 'space-y-1 p-1.5 lg:space-y-1.5 lg:p-3'"
            :aria-label="$t('docetra.recordLogBoard.tabsTitle')"
          >
            <UTooltip
              v-for="tab in tabs"
              :key="tab.id"
              :text="$t(tab.labelKey)"
              :content="{ side: 'right', sideOffset: 8 }"
            >
              <button
                type="button"
                class="flex w-full items-center transition"
                :class="[
                  mobileLogListOpen
                    ? 'gap-2 rounded-lg border px-2.5 py-2 text-left'
                    : leftCollapsed
                    ? 'justify-center rounded-md p-2'
                    : 'justify-center rounded-md p-2 lg:justify-start lg:gap-2 lg:rounded-lg lg:border lg:px-2.5 lg:py-2 lg:text-left',
                  selectedTabId === tab.id
                    ? (mobileLogListOpen
                        ? 'border-primary bg-primary/5 ring-1 ring-primary/25'
                        : leftCollapsed
                        ? 'bg-primary/10 text-primary ring-1 ring-primary/30'
                        : 'bg-primary/10 text-primary ring-1 ring-primary/30 lg:border-primary lg:bg-primary/5 lg:text-inherit lg:ring-primary/25')
                    : (mobileLogListOpen
                        ? 'border-default hover:border-primary/30'
                        : leftCollapsed
                        ? 'text-muted hover:bg-elevated hover:text-highlighted'
                        : 'text-muted hover:bg-elevated hover:text-highlighted lg:border-default lg:text-inherit lg:hover:border-primary/30 lg:hover:bg-transparent'),
                ]"
                :aria-label="$t(tab.labelKey)"
                :aria-current="selectedTabId === tab.id ? 'page' : undefined"
                @click="selectLogTab(tab.id)"
              >
                <UIcon
                  :name="tab.icon"
                  class="size-4 shrink-0"
                  :class="selectedTabId === tab.id ? 'text-primary' : 'text-muted'"
                />

                <template v-if="mobileLogListOpen || !leftCollapsed">
                  <span
                    class="min-w-0 flex-1 truncate text-sm"
                    :class="[
                      mobileLogListOpen ? '' : 'hidden lg:block',
                      selectedTabId === tab.id ? 'font-semibold text-highlighted' : 'font-medium text-toned',
                    ]"
                  >
                    {{ $t(tab.labelKey) }}
                  </span>
                  <UBadge
                    color="neutral"
                    variant="subtle"
                    size="sm"
                    class="shrink-0 tabular-nums"
                    :class="mobileLogListOpen ? '' : 'hidden lg:inline-flex'"
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
          <div class="flex shrink-0 items-center gap-2 border-b border-default px-4 py-3.5">
            <div class="flex min-w-0 shrink-0 items-center gap-1.5">
              <UButton
                icon="i-lucide-menu"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                class="shrink-0 lg:hidden"
                :aria-label="$t('docetra.recordLogBoard.tabsTitle')"
                :aria-expanded="mobileLogListOpen"
                @click="mobileLogListOpen = true"
              />
              <UButton
                :icon="leftCollapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
                color="neutral"
                variant="ghost"
                size="sm"
                square
                class="hidden shrink-0 lg:inline-flex"
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

            <CommonAppLiveSearch
              v-model="search"
              class="hidden min-w-0 w-full max-w-[18.75rem] flex-1 lg:flex"
              :placeholder="$t('docetra.recordLogBoard.search')"
            />

            <div class="ms-auto hidden shrink-0 lg:block">
              <CommonAppDateRangeFilter
                v-model:start="dateStart"
                v-model:end="dateEnd"
                :label="$t('docetra.fields.occurredAt')"
                size="sm"
              />
            </div>
            <UPopover class="ms-auto shrink-0 lg:hidden">
              <UButton
                icon="i-lucide-filter"
                :color="hasLogFilters ? 'primary' : 'neutral'"
                :variant="hasLogFilters ? 'soft' : 'outline'"
                size="sm"
                square
                :aria-label="$t('docetra.actions.filter')"
              />
              <template #content>
                <div class="flex w-[calc(100vw-2rem)] flex-nowrap items-center gap-2 overflow-x-auto p-3">
                  <CommonAppLiveSearch
                    v-model="search"
                    class="w-[18.75rem] shrink-0"
                    :placeholder="$t('docetra.recordLogBoard.search')"
                  />
                  <CommonAppDateRangeFilter
                    v-model:start="dateStart"
                    v-model:end="dateEnd"
                    :label="$t('docetra.fields.occurredAt')"
                    size="sm"
                    inline
                  />
                </div>
              </template>
            </UPopover>
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
            :row-actions="[
              { key: 'detail', labelKey: 'docetra.rowActions.detail', icon: 'i-lucide-eye' },
              { key: 'logs', labelKey: 'docetra.rowActions.logs', icon: 'i-lucide-scroll-text' },
            ]"
            @update:page="page = $event"
            @update:limit="limit = $event"
            @row-click="openRow"
            @row-action="({ key, row }) => key === 'detail' || key === 'logs' ? openRow(row) : undefined"
            @retry="refresh"
          />
        </section>
      </div>
    </div>
  </WorkspaceAppWorkspacePage>
</template>

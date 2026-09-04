<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { BoardViewMode } from '~/composables/common/useBoardViewMode'
import type { FilterDef } from '~/types/docetra/common'

/**
 * Shared two-pane board chrome: collapsible rail (drawer on mobile) +
 * right-panel header (panel toggles, title, search, date range, card/table toggle).
 * Boards supply rail pills/items and content via slots; domain logic stays
 * in each board's composable.
 */
const props = withDefaults(defineProps<{
  railTitleKey: string
  railIcon: string
  collapsed: boolean
  mobileOpen: boolean
  /** Right-panel heading (selected stage/topic label). Omit to hide. */
  headerTitle?: string
  /** Collapse/expand aria-label keys for the right panel toggles. */
  expandLabelKey: string
  collapseLabelKey: string
  railSearch?: string
  railSearchPlaceholderKey?: string
  headerSearch?: string
  headerSearchPlaceholderKey?: string
  dateStart?: string
  dateEnd?: string
  /** When bound, shows cards/table toggle in the header. */
  viewMode?: BoardViewMode
  pending?: boolean
  /** Gate for the first-load overlay (e.g. `pending && !items.length`). */
  showPendingOverlay?: boolean
  error?: string
}>(), {
  pending: false,
  showPendingOverlay: false,
})

const emit = defineEmits<{
  'update:collapsed': [value: boolean]
  'update:mobileOpen': [value: boolean]
  'update:railSearch': [value: string]
  'update:headerSearch': [value: string]
  'update:dateStart': [value: string]
  'update:dateEnd': [value: string]
  'update:viewMode': [value: BoardViewMode]
  retry: []
}>()

const isSmallScreen = useMediaQuery('(max-width: 1023px)')
/** Desktop only: icon rail when collapsed. Small screens never use an icon rail. */
const railCollapsed = computed(() =>
  isSmallScreen.value ? false : props.collapsed,
)

const showViewToggle = computed(() => props.viewMode !== undefined)

const { t } = useI18n()

/** Hide labels below sm (≤ 639 px) so the toggle stays icon-only on small screens. */
const isVerySmall = useMediaQuery('(max-width: 639px)')

const viewItems = computed(() => [
  {
    label: isVerySmall.value ? '' : t('docetra.views.cards'),
    value: 'cards',
    icon: 'i-lucide-layout-grid',
  },
  {
    label: isVerySmall.value ? '' : t('docetra.views.table'),
    value: 'table',
    icon: 'i-lucide-table',
  },
])

const dateFilter: FilterDef = {
  key: 'dateRange',
  labelKey: 'docetra.fields.meetingDate',
  type: 'daterange',
}

function closeMobile() {
  emit('update:mobileOpen', false)
}

function onViewModeChange(value: string | number) {
  const mode = String(value) as BoardViewMode
  if (mode !== 'cards' && mode !== 'table') return
  if (props.viewMode === mode) return
  emit('update:viewMode', mode)
}
</script>

<template>
  <div class="relative flex min-h-0 flex-1 flex-col overflow-hidden rounded-sm border border-default bg-default">
    <div
      v-if="showPendingOverlay"
      class="absolute inset-0 z-10 flex items-center justify-center bg-default/50"
    >
      <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
    </div>

    <UAlert
      v-if="error"
      class="m-3"
      color="error"
      :title="error"
      :actions="[{ label: $t('docetra.actions.retry'), onClick: () => emit('retry') }]"
    />

    <slot name="alerts" />

    <div class="relative flex min-h-0 flex-1 flex-row overflow-hidden">
      <button
        v-if="isSmallScreen && mobileOpen"
        type="button"
        class="absolute inset-0 z-20 bg-black/25 lg:hidden"
        :aria-label="$t('actions.close')"
        @click="closeMobile"
      />

      <!-- Left rail: overlay drawer on small screens (no icon rail); collapsible rail on lg+ -->
      <aside
        class="flex h-full min-h-0 shrink-0 flex-col overflow-hidden border-e border-default bg-default transition-[width] duration-200 lg:static lg:z-auto lg:shadow-none"
        :class="isSmallScreen
          ? (mobileOpen
              ? 'absolute inset-y-0 inset-s-0 z-30 w-[min(22rem,calc(100%-3rem))] shadow-xl'
              : 'hidden')
          : ''"
        :style="isSmallScreen
          ? undefined
          : { width: railCollapsed ? '3.5rem' : 'min(22rem, calc(100% - 3rem))' }"
      >
        <div
          class="shrink-0 space-y-2 border-b border-default"
          :class="railCollapsed ? 'space-y-1.5 px-1.5 py-3.5' : 'px-3 py-2.5'"
        >
          <div v-if="!railCollapsed" class="flex items-center justify-between gap-2">
            <h2 class="min-w-0 truncate text-sm font-semibold text-highlighted">
              {{ $t(railTitleKey) }}
            </h2>
            <UButton
              icon="i-lucide-panel-left-close"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="shrink-0 lg:hidden"
              :aria-label="$t('actions.close')"
              @click="closeMobile"
            />
          </div>
          <div v-else class="flex justify-center">
            <UIcon :name="railIcon" class="size-4 text-muted" />
          </div>

          <CommonAppLiveSearch
            v-if="!railCollapsed && railSearch !== undefined"
            :model-value="railSearch"
            size="md"
            class="w-full"
            :placeholder="railSearchPlaceholderKey ? $t(railSearchPlaceholderKey) : $t('common.search')"
            @update:model-value="(v: string) => emit('update:railSearch', v)"
          />

          <slot name="rail-pills" />
        </div>

        <div
          class="min-h-0 flex-1 overflow-y-auto overflow-x-hidden"
          :class="railCollapsed ? 'space-y-1 p-1.5' : 'space-y-2 p-3'"
        >
          <slot name="rail-items" />
        </div>
      </aside>

      <!-- Right panel -->
      <section class="flex min-h-0 min-w-0 flex-1 flex-col overflow-hidden">
        <div class="flex shrink-0 items-center gap-2 border-b border-default px-3 py-2.5 sm:px-4 sm:py-3.5">
          <div class="flex min-w-0 shrink-0 items-center gap-1.5">
            <UButton
              :icon="mobileOpen ? 'i-lucide-panel-left-close' : 'i-lucide-panel-left-open'"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="shrink-0 lg:hidden"
              :aria-label="$t(railTitleKey)"
              :aria-expanded="mobileOpen"
              @click="emit('update:mobileOpen', !mobileOpen)"
            />
            <UButton
              :icon="collapsed ? 'i-lucide-panel-left-open' : 'i-lucide-panel-left-close'"
              color="neutral"
              variant="ghost"
              size="sm"
              square
              class="hidden shrink-0 lg:inline-flex"
              :aria-label="$t(collapsed ? expandLabelKey : collapseLabelKey)"
              :aria-expanded="!collapsed"
              @click="emit('update:collapsed', !collapsed)"
            />
            <h2
              v-if="headerTitle"
              class="hidden min-w-0 max-w-40 truncate text-sm font-semibold text-highlighted sm:block"
            >
              {{ headerTitle }}
            </h2>
          </div>

          <CommonAppLiveSearch
            v-if="headerSearch !== undefined"
            :model-value="headerSearch"
            size="md"
            class="min-w-0 w-full max-w-75 flex-1"
            :placeholder="headerSearchPlaceholderKey ? $t(headerSearchPlaceholderKey) : $t('common.search')"
            @update:model-value="(v: string) => emit('update:headerSearch', v)"
          />
          <slot name="header-extra" />

          <UTabs
            v-if="showViewToggle"
            :model-value="viewMode"
            :items="viewItems"
            :content="false"
            size="sm"
            class="shrink-0"
            :aria-label="$t('docetra.views.toggle')"
            @update:model-value="onViewModeChange"
          />

          <CommonAppFilterControl
            v-if="dateStart !== undefined"
            :filter="dateFilter"
            :start="dateStart"
            :end="dateEnd ?? ''"
            class="ms-auto shrink-0"
            size="md"
            @update:start="(v: string) => emit('update:dateStart', v)"
            @update:end="(v: string) => emit('update:dateEnd', v)"
          />
        </div>

        <slot />
      </section>
    </div>
  </div>
</template>

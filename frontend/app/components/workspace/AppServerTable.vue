<script setup lang="ts">
import { h, resolveComponent } from 'vue'
import type { TableColumn } from '@nuxt/ui'
import type { Row, RowSelectionState } from '@tanstack/vue-table'
import type { TableColumnDef } from '~/types/docetra/common'
import type { RowActionItem } from '~/types/docetra/row-actions'
import { DEFAULT_ROW_ACTIONS } from '~/types/docetra/row-actions'
import {
  TABLE_PAGE_SIZES,
  paginationItemsPerPage,
  parsePageLimit,
} from '~/utils/pagination'

type DataRow = Record<string, unknown>

const props = withDefaults(defineProps<{
  columns: TableColumnDef[]
  rows: DataRow[]
  total: number
  page: number
  limit: number
  pending?: boolean
  error?: string | null
  cellValue: (row: DataRow, key: string) => string
  canDelete?: boolean
  /** Row checkboxes. Off for read-only audit lists. */
  selectable?: boolean
  /** Owner/comments meta rail. Off for log tables. */
  showMeta?: boolean
  /** Per-row ⋯ action menu. Pass `false` to hide. */
  rowActions?: RowActionItem[] | false
}>(), {
  selectable: true,
  showMeta: true,
  rowActions: () => DEFAULT_ROW_ACTIONS,
})

const emit = defineEmits<{
  'update:page': [number]
  'update:limit': [number]
  'update:selection': [string[]]
  rowClick: [DataRow]
  deleteSelected: [string[]]
  rowAction: [payload: { key: string, row: DataRow }]
  retry: []
}>()

const { t } = useI18n()

const UBadge = resolveComponent('UBadge')
const UButton = resolveComponent('UButton')
const UCheckbox = resolveComponent('UCheckbox')
const UIcon = resolveComponent('UIcon')
const AppTableRowMeta = resolveComponent('WorkspaceAppTableRowMeta')
const AppRowActionsMenu = resolveComponent('CommonAppRowActionsMenu')

const resolvedRowActions = computed(() => {
  if (props.rowActions === false) return null
  const actions = [...(props.rowActions || DEFAULT_ROW_ACTIONS)]
  if (props.canDelete === false) {
    return actions.filter(action => action.key !== 'delete')
  }
  return actions
})

const rowSelection = ref<RowSelectionState>({})

const pageSizeItems = computed(() => [
  ...TABLE_PAGE_SIZES.map(size => ({ label: String(size), value: String(size) })),
])

const pageSizeModel = computed({
  get: () => String(props.limit),
  set: value => onLimitChange(value),
})

const effectiveItemsPerPage = computed(() =>
  paginationItemsPerPage(props.limit, props.total),
)

const visibleRange = computed(() => {
  if (!props.total || !props.rows.length) return { start: 0, end: 0 }
  const start = ((props.page - 1) * props.limit) + 1
  return {
    start,
    end: Math.min(start + props.rows.length - 1, props.total),
  }
})

const allVisibleSelected = computed(() => {
  if (!props.rows.length) return false
  return props.rows.every(row => rowSelection.value[String(row.id)])
})

const metaHeaderLabel = computed(() => {
  const assigned = props.rows.filter(row =>
    asPerson(row.assignee)
    || asPerson(row.owner)
    || asPerson(row.updatedBy)
    || asPerson(row.createdBy)
    || asPerson(row.actor)
    || asPerson(row.uploader),
  ).length
  const total = props.rows.length || 0
  return `${assigned} of ${total}`
})

const selectedIds = computed(() =>
  Object.entries(rowSelection.value)
    .filter(([, selected]) => selected)
    .map(([id]) => id),
)

const selectedCount = computed(() => selectedIds.value.length)

watch(selectedIds, (ids) => {
  emit('update:selection', ids)
}, { deep: true })

watch(() => [props.page, props.limit, props.rows], () => {
  rowSelection.value = {}
})

function onLimitChange(value: unknown) {
  const nextLimit = parsePageLimit(value, 10)
  if (nextLimit === props.limit && props.page === 1) return
  emit('update:page', 1)
  emit('update:limit', nextLimit)
}

function selectAllVisibleRows() {
  const next: RowSelectionState = {}
  for (const row of props.rows) {
    next[String(row.id)] = true
  }
  rowSelection.value = next
}

function isNumericCol(key: string) {
  return /amount|rate|total|count|size|bytes|qty|quantity|number/i.test(key)
}

function cellMode(col: TableColumnDef) {
  if (col.cell) return col.cell
  const key = col.key
  if (key === 'status' || key === 'stage' || key === 'level' || key === 'action' || key === 'severity' || key === 'entityType') {
    return 'badge'
  }
  if (key.endsWith('At') || key.endsWith('Date') || key === 'occurredAt') return 'datetime'
  if (key.endsWith('.name') && (key.startsWith('actor') || key.startsWith('owner') || key.startsWith('assignee'))) {
    return 'person'
  }
  return 'text'
}

function badgeColor(key: string, raw: unknown): 'primary' | 'secondary' | 'success' | 'info' | 'warning' | 'error' | 'neutral' {
  const value = String(raw || '').toLowerCase()
  if (key === 'action') {
    if (value === 'created') return 'success'
    if (value === 'updated') return 'info'
    if (value === 'stage_changed') return 'warning'
    if (value === 'shared') return 'secondary'
    return 'neutral'
  }
  if (key === 'severity' || key === 'level') {
    if (value === 'error') return 'error'
    if (value === 'warn' || value === 'warning') return 'warning'
    if (value === 'info') return 'info'
    if (value === 'debug') return 'neutral'
    return 'neutral'
  }
  if (key === 'entityType') {
    if (value.includes('incoming')) return 'info'
    if (value.includes('outgoing')) return 'secondary'
    if (value.includes('master')) return 'warning'
    return 'primary'
  }
  if (key === 'isActive' || key === 'authenticationEnabled') {
    return value === 'true' ? 'success' : 'error'
  }
  if (key === 'status') {
    if (value === 'completed' || value === 'active') return 'success'
    if (value === 'pending' || value === 'draft') return 'warning'
    if (value === 'failed' || value === 'disabled') return 'error'
    return 'neutral'
  }
  if (key === 'stage' || key === 'recordStage') {
    if (value === 'completed') return 'success'
    if (value === 'approval') return 'primary'
    if (value === 'review') return 'warning'
    return 'info'
  }
  return 'neutral'
}

function asPerson(value: unknown) {
  if (value && typeof value === 'object' && 'name' in (value as object)) {
    return value as { id?: string, name: string, email?: string, avatarUrl?: string }
  }
  return null
}

function rawCellValue(row: DataRow, key: string) {
  return key.split('.').reduce<unknown>((acc, part) => {
    if (acc && typeof acc === 'object' && part in (acc as object)) {
      return (acc as Record<string, unknown>)[part]
    }
    return undefined
  }, row)
}

function clearSelection() {
  rowSelection.value = {}
}

function requestDelete() {
  if (!selectedIds.value.length) return
  emit('deleteSelected', [...selectedIds.value])
}

const tableColumns = computed<TableColumn<DataRow>[]>(() => {
  const cols: TableColumn<DataRow>[] = []

  if (props.selectable) {
    cols.push({
      id: 'select',
      header: () => {
        const some = selectedCount.value > 0 && !allVisibleSelected.value
        return h(UCheckbox, {
          'modelValue': some ? 'indeterminate' : allVisibleSelected.value,
          'onUpdate:modelValue': (value: boolean | 'indeterminate') => {
            if (value) selectAllVisibleRows()
            else clearSelection()
          },
          'aria-label': t('docetra.actions.selectAll'),
          'onClick': (e: Event) => e.stopPropagation(),
        })
      },
      size: 44,
      meta: {
        class: {
          th: 'w-11 min-w-11 text-center border-e border-default',
          td: 'w-11 min-w-11 text-center border-e border-default',
        },
      },
      cell: ({ row }) => h(UCheckbox, {
        'modelValue': row.getIsSelected(),
        'disabled': !row.getCanSelect(),
        'onUpdate:modelValue': (value: boolean | 'indeterminate') =>
          row.toggleSelected(!!value),
        'aria-label': t('docetra.actions.selectRow'),
        'onClick': (e: Event) => e.stopPropagation(),
      }),
    })
  }

  cols.push(...props.columns.map((col): TableColumn<DataRow> => ({
    id: col.key,
    accessorKey: col.key,
    header: t(col.labelKey),
    meta: {
      class: {
        th: [
          'border-e border-default whitespace-nowrap text-center',
          col.priority === 'low' ? 'hidden md:table-cell' : '',
          col.priority === 'medium' ? 'hidden sm:table-cell' : '',
        ].filter(Boolean).join(' '),
        td: [
          'border-e border-default whitespace-nowrap',
          isNumericCol(col.key) ? 'text-end tabular-nums' : 'text-start',
          col.priority === 'low' ? 'hidden md:table-cell' : '',
          col.priority === 'medium' ? 'hidden sm:table-cell' : '',
          col.key === 'summary' ? 'max-w-xs truncate' : '',
        ].filter(Boolean).join(' '),
      },
    },
    cell: ({ row }) => {
      const value = props.cellValue(row.original, col.key)
      const mode = cellMode(col)
      if (mode === 'badge') {
        const raw = rawCellValue(row.original, col.key)
        return h(UBadge, {
          color: badgeColor(col.key, raw),
          variant: 'subtle',
          size: 'sm',
        }, () => value)
      }
      return value || '—'
    },
  })))

  if (props.showMeta) {
    cols.push({
      id: 'meta',
      header: () => h('div', {
        class: 'flex w-full items-center justify-end gap-1.5 text-xs font-medium text-toned',
      }, [
        h('span', { class: 'tabular-nums' }, metaHeaderLabel.value),
        h(UIcon, { name: 'i-lucide-heart', class: 'size-3.5 text-muted' }),
      ]),
      size: 140,
      meta: {
        class: {
          th: 'w-36 min-w-36',
          td: 'w-36 min-w-36',
        },
      },
      cell: ({ row }) => {
        const owner = asPerson(row.original.owner)
          || asPerson(row.original.assignee)
          || asPerson(row.original.updatedBy)
          || asPerson(row.original.createdBy)
          || asPerson(row.original.actor)
          || asPerson(row.original.uploader)
        return h(AppTableRowMeta, {
          owner,
          updatedAt: row.original.updatedAt ? String(row.original.updatedAt) : undefined,
          commentCount: Number(row.original.commentCount || 0),
          liked: Boolean(row.original.liked),
        })
      },
    })
  }

  if (resolvedRowActions.value?.length) {
    cols.push({
      id: 'actions',
      header: () => '',
      size: 48,
      meta: {
        class: {
          th: 'w-12 min-w-12 sticky end-0 z-10 bg-muted',
          td: 'w-12 min-w-12 sticky end-0 z-[1] bg-default',
        },
      },
      cell: ({ row }) => h('div', {
        class: 'flex justify-center',
        onClick: (e: Event) => e.stopPropagation(),
      }, [
        h(AppRowActionsMenu, {
          row: row.original,
          actions: resolvedRowActions.value!,
          alwaysVisible: true,
          onAction: (payload: { key: string, row: DataRow }) => {
            emit('rowAction', payload)
          },
        }),
      ]),
    })
  }

  return cols
})

function onSelect(e: Event, row: Row<DataRow>) {
  const target = e.target as HTMLElement | null
  if (target?.closest('[role="checkbox"], button, a, input, [data-reka-dropdown-menu-content], [role="menu"]')) return
  emit('rowClick', row.original)
}

defineExpose({
  clearSelection,
  selectedIds,
})
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden">
    <slot name="toolbar" />

    <div
      v-if="selectedCount"
      class="flex shrink-0 items-center justify-between gap-3 border-b border-default bg-muted/50 px-3 py-2"
    >
      <div class="flex items-center gap-2 text-sm text-toned">
        <UIcon name="i-lucide-check-square" class="size-4 text-highlighted" />
        <span>{{ $t('docetra.actions.itemsSelected', { n: selectedCount }) }}</span>
      </div>
      <div class="flex items-center gap-2">
        <UButton
          v-if="!allVisibleSelected && rows.length"
          color="neutral"
          variant="soft"
          size="xs"
          icon="i-lucide-check-check"
          :label="$t('docetra.actions.selectAllRows', { n: rows.length })"
          @click="selectAllVisibleRows"
        />
        <UButton
          v-if="canDelete !== false"
          color="error"
          variant="soft"
          size="xs"
          icon="i-lucide-trash-2"
          :label="$t('actions.delete')"
          @click="requestDelete"
        />
        <UButton
          color="neutral"
          variant="ghost"
          size="xs"
          :label="$t('actions.cancel')"
          @click="clearSelection"
        />
      </div>
    </div>

    <div v-if="error" class="flex shrink-0 items-center justify-between gap-3 border-b border-default p-3">
      <p class="text-sm text-error">{{ error }}</p>
      <UButton size="sm" @click="emit('retry')">{{ $t('docetra.actions.retry') }}</UButton>
    </div>

    <UTable
      v-else
      v-model:row-selection="rowSelection"
      sticky="header"
      :virtualize="{ estimateSize: 44, overscan: 20 }"
      :data="rows"
      :columns="tableColumns"
      :loading="pending"
      loading-color="primary"
      :empty="$t('docetra.states.empty')"
      :get-row-id="(row) => String(row.id)"
      class="min-h-0 flex-1"
      :ui="{
        root: 'relative overflow-auto',
        base: 'min-w-max w-full border-separate border-spacing-0',
        thead: '[&_tr]:border-b-0',
        tbody: 'divide-y-0',
        tr: 'group cursor-pointer hover:bg-muted/40 data-[selected=true]:bg-elevated/60',
        th: 'sticky top-0 z-10 bg-muted px-2.5 py-2.5 text-xs font-bold text-highlighted border-b border-default',
        td: 'px-2.5 py-2 text-sm text-highlighted border-b border-default',
        empty: 'py-12 text-center text-muted',
      }"
      @select="onSelect"
    />

    <div
      v-if="!error"
      class="flex shrink-0 items-center justify-between gap-1.5 border-t border-default bg-default px-2 py-1.5 sm:gap-3 sm:px-3 sm:py-2"
    >
      <div class="flex shrink-0 items-center gap-1.5 text-sm text-toned sm:gap-2">
        <span class="hidden sm:inline">{{ $t('common.rowsPerPage') }}</span>
        <USelect
          v-model="pageSizeModel"
          :items="pageSizeItems"
          value-key="value"
          size="sm"
          class="w-17 sm:w-22"
          :content="{ side: 'top', align: 'start', sideOffset: 6 }"
          :aria-label="$t('common.rowsPerPage')"
          :ui="{ base: 'rounded-md bg-default ring-1 ring-default' }"
        />
        <span class="hidden whitespace-nowrap text-xs text-muted md:inline">
          {{ $t('common.showingRows', { start: visibleRange.start, end: visibleRange.end, total }) }}
        </span>
      </div>

      <UPagination
        :page="page"
        :total="total"
        :items-per-page="effectiveItemsPerPage"
        :sibling-count="0"
        show-edges
        size="sm"
        color="neutral"
        variant="outline"
        active-color="primary"
        active-variant="solid"
        first-icon="i-lucide-chevrons-left"
        prev-icon="i-lucide-chevron-left"
        next-icon="i-lucide-chevron-right"
        last-icon="i-lucide-chevrons-right"
        :ui="{
          list: 'gap-0.5 sm:gap-1',
          item: 'min-w-7 h-7 justify-center rounded-md sm:min-w-8 sm:h-8',
          first: 'hidden rounded-md sm:inline-flex',
          prev: 'rounded-md',
          next: 'rounded-md',
          last: 'hidden rounded-md sm:inline-flex',
        }"
        @update:page="(v: number) => emit('update:page', v)"
      />
    </div>
  </div>
</template>

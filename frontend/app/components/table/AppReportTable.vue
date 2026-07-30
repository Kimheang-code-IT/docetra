<script setup lang="ts" generic="T extends Record<string, any>">
import { computed, ref, toRef, useSlots } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { ACTION_COL_WIDTH, ACTION_HEADER, type ReportColumn } from '~/constants/report-table'
import { actionColStyle, colWidthStyle, stickyColStyle } from '~/utils/table/report-table-layout'
import { useReportTableStickyOffsets } from '~/composables/table/useReportTableStickyOffsets'
import {
  REPORT_FOOTER_LABEL,
  computeReportColumnTotals,
  getFooterIdentityMergeCount,
  sumMergedColumnWidths,
  resolveReportFooterCell,
} from '~/utils/table/report-footer'
import { createDefaultPaginationState } from '~/utils/api/pagination'

const props = withDefaults(defineProps<{
  columns?: ReportColumn[]
  data?: T[]
  total?: number
  rowKey?: string
  getRowActions?: (item: T) => DropdownMenuItem[][]
  formatCell?: (row: T, key: string) => string
  stickyLeftCount?: number
  showPagination?: boolean
  showActions?: boolean
  actionHeader?: string
  emptyColspan?: number
  showFooterTotals?: boolean
  footerData?: T[]
  footerLabel?: string
}>(), {
  data: () => [],
  rowKey: 'id',
  stickyLeftCount: 0,
  showPagination: true,
  showActions: true,
  actionHeader: ACTION_HEADER,
  showFooterTotals: false,
  footerLabel: REPORT_FOOTER_LABEL,
})

const pagination = defineModel<{ pageIndex: number; pageSize: number }>('pagination', {
  default: createDefaultPaginationState,
})

const slots = useSlots()

const isCustomMode = computed(() => !!(slots.header || slots.body))
const hasActions = computed(() => props.showActions && !!props.getRowActions)
const columns = computed(() => props.columns ?? [])

const scrollRef = ref<HTMLElement>()
const { stickyOffsets } = useReportTableStickyOffsets(
  scrollRef,
  computed(() => props.stickyLeftCount),
  [toRef(props, 'data')],
)

const totalColumnCount = computed(() => {
  if (props.emptyColspan) return props.emptyColspan
  return columns.value.length + (hasActions.value ? 1 : 0)
})

function colStyle(col: ReportColumn) {
  return colWidthStyle(col.width)
}

function stickyStyle(index: number, isHeader = false) {
  const col = columns.value[index]
  if (!col) return {}
  return stickyColStyle(stickyOffsets.value[index] ?? 0, col.width, isHeader, index)
}

function isStickyIndex(index: number) {
  return index < props.stickyLeftCount
}

function rowId(row: T) {
  return String(row[props.rowKey])
}

function defaultCellValue(row: T, col: ReportColumn) {
  if (props.formatCell) return props.formatCell(row, col.key)
  const value = row[col.key]
  if (value == null || value === '') return '—'
  return String(value)
}

const footerRows = computed(() => props.footerData ?? props.data)

const showFooter = computed(() =>
  props.showFooterTotals && footerRows.value.length > 0 && columns.value.length > 0,
)

const footerIdentityMergeCount = computed(() =>
  getFooterIdentityMergeCount(columns.value.map((col) => col.key)),
)

const footerMergeColStyle = computed(() => {
  const widths = columns.value.map((col) => col.width)
  const mergeWidth = sumMergedColumnWidths(widths, footerIdentityMergeCount.value)
  const base = colWidthStyle(mergeWidth)
  if (props.stickyLeftCount > 0) {
    return { ...base, ...stickyStyle(0, true) }
  }
  return base
})

const footerTotals = computed(() =>
  computeReportColumnTotals(footerRows.value as Record<string, unknown>[], columns.value),
)

function footerCellValue(col: ReportColumn, index: number) {
  if (index < footerIdentityMergeCount.value) return ''
  return resolveReportFooterCell(col, {
    totals: footerTotals.value,
    labelColumnKey: null,
    rowCount: footerRows.value.length,
    formatCell: props.formatCell,
    footerLabel: props.footerLabel,
  })
}
</script>

<template>
  <div class="app-report-table flex flex-col w-full h-full overflow-hidden rounded-xs">
    <div ref="scrollRef" class="flex-1 min-h-0 overflow-auto app-report-table__scroll">
      <table class="app-report-table__grid">
        <thead v-if="isCustomMode && $slots.header" class="app-report-table__thead">
          <slot name="header" />
        </thead>
        <thead v-else-if="columns.length" class="app-report-table__thead">
          <tr>
            <th
              v-for="(col, index) in columns"
              :key="`head-${col.key}`"
              class="app-report-table__th"
              :class="{ 'app-report-table__th--sticky': isStickyIndex(index) }"
              :style="isStickyIndex(index) ? stickyStyle(index, true) : colStyle(col)"
            >
              {{ col.label }}
            </th>
            <th
              v-if="hasActions"
              class="app-report-table__th app-report-table__th--action"
              :style="actionColStyle(true)"
            >
              {{ actionHeader }}
            </th>
          </tr>
          <tr v-if="showFooter" class="app-report-table__row app-report-table__row--total">
            <th
              v-if="footerIdentityMergeCount > 0"
              :colspan="footerIdentityMergeCount"
              class="app-report-table__th app-report-table__th--total app-report-table__th--text"
              :class="{ 'app-report-table__th--sticky': stickyLeftCount > 0 }"
              :style="footerMergeColStyle"
            >
              {{ footerLabel }}
            </th>
            <th
              v-for="(col, index) in columns.slice(footerIdentityMergeCount)"
              :key="`foot-${col.key}`"
              class="app-report-table__th app-report-table__th--total"
              :class="{
                'app-report-table__th--sticky': isStickyIndex(index + footerIdentityMergeCount),
                'app-report-table__th--text': col.text,
                'app-report-table__th--numeric': col.numeric,
              }"
              :style="isStickyIndex(index + footerIdentityMergeCount)
                ? stickyStyle(index + footerIdentityMergeCount, true)
                : colStyle(col)"
            >
              {{ footerCellValue(col, index + footerIdentityMergeCount) }}
            </th>
            <th
              v-if="hasActions"
              class="app-report-table__th app-report-table__th--total app-report-table__th--action"
              :style="actionColStyle(true)"
            >
              —
            </th>
          </tr>
        </thead>

        <tbody v-if="isCustomMode && $slots.body">
          <slot name="body" />
        </tbody>
        <tbody v-else>
          <tr v-for="row in data" :key="rowId(row)" class="app-report-table__row">
            <td
              v-for="(col, index) in columns"
              :key="`body-${rowId(row)}-${col.key}`"
              class="app-report-table__td"
              :class="{
                'app-report-table__td--sticky': isStickyIndex(index),
                'app-report-table__td--text': col.text,
                'app-report-table__td--numeric': col.numeric,
              }"
              :style="isStickyIndex(index) ? stickyStyle(index) : colStyle(col)"
            >
              <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">
                {{ defaultCellValue(row, col) }}
              </slot>
            </td>
            <td
              v-if="hasActions"
              class="app-report-table__td app-report-table__td--action"
              :style="actionColStyle()"
            >
              <UDropdownMenu
                v-if="getRowActions"
                :items="getRowActions(row)"
                :content="{ align: 'end' }"
              >
                <UButton
                  icon="i-lucide-ellipsis-vertical"
                  color="neutral"
                  variant="ghost"
                  size="sm"
                  class="rounded-md"
                />
              </UDropdownMenu>
            </td>
          </tr>
          <tr v-if="!data.length">
            <td :colspan="totalColumnCount" class="app-report-table__td app-report-table__td--empty">
              <slot name="empty">
                <CommonAppTableEmptyState />
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <ClientOnly v-if="showPagination">
      <CommonAppFooterPagin
        v-model:pagination="pagination"
        :total="total ?? data.length"
        :selectable="false"
      />
    </ClientOnly>
  </div>
</template>

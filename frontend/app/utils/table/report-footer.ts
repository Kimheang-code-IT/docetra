import type { ReportColumn } from '~/constants/report-table'

export const REPORT_FOOTER_LABEL = 'សរុបរួម'

/** Identity columns merged into one label cell in the total row */
export const FOOTER_IDENTITY_KEYS = ['id', 'departmentCode', 'departmentName'] as const

export function getFooterIdentityMergeCount(columnKeys: readonly string[]): number {
  let count = 0
  for (const expected of FOOTER_IDENTITY_KEYS) {
    if (columnKeys[count] === expected) count++
    else break
  }
  if (count === 1 && (columnKeys[1] === 'entityName' || columnKeys[1] === 'departmentName')) {
    return 2
  }
  if (
    columnKeys[0] === 'id'
    && columnKeys[1] === 'departmentCode'
    && (columnKeys[2] === 'departmentName' || columnKeys[2] === 'entityName')
  ) {
    return 3
  }
  return count
}

export function sumMergedColumnWidths(widths: readonly number[], mergeCount: number): number {
  return widths.slice(0, mergeCount).reduce((sum, width) => sum + width, 0)
}

export function sumField<T extends Record<string, unknown>>(rows: T[], key: string): number {
  return rows.reduce((acc, row) => acc + Number(row[key] ?? 0), 0)
}

export function isPercentColumnKey(key: string): boolean {
  return /percent/i.test(key)
}

export function isCountColumnKey(key: string): boolean {
  return /count|paymentCount/i.test(key)
}

export function computeReportColumnTotals<T extends Record<string, unknown>>(
  rows: T[],
  columns: ReportColumn[],
): Record<string, number> {
  const totals: Record<string, number> = {}
  for (const col of columns) {
    if (col.numeric && !isPercentColumnKey(col.key)) {
      totals[col.key] = sumField(rows, col.key)
    }
  }
  return totals
}

export function findReportFooterLabelColumn(columns: ReportColumn[]): string | null {
  return columns.find((col) => col.text)?.key
    ?? columns.find((col) => col.key === 'departmentName')?.key
    ?? columns.find((col) => col.key === 'entityName')?.key
    ?? null
}

export function resolveReportFooterCell<T extends Record<string, unknown>>(
  col: ReportColumn,
  options: {
    totals: Record<string, number>
    labelColumnKey: string | null
    rowCount: number
    formatCell?: (row: T, key: string) => string
    footerLabel?: string
  },
): string {
  const label = options.footerLabel ?? REPORT_FOOTER_LABEL

  if (col.key === options.labelColumnKey) return label
  if (col.key === 'id') return String(options.rowCount)
  if (col.numeric && options.totals[col.key] !== undefined) {
    const value = options.totals[col.key]!
    if (options.formatCell) {
      return options.formatCell({ [col.key]: value } as T, col.key)
    }
    return String(value)
  }
  return '—'
}

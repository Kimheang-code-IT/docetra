const CHART_FONT_FAMILY = '"Noto Sans Khmer", "Khmer OS Siemreap", "Inter", sans-serif'

type EChartOption = Record<string, unknown>

export interface ChartLegendLayout {
  itemCount: number
  rows: number
  legend: Record<string, unknown>
  gridBottom: number | string
  pieLiftPercent: number
}

function parsePercent(value: unknown, fallback = 0): number {
  if (typeof value === 'number') return value
  const parsed = Number.parseFloat(String(value))
  return Number.isNaN(parsed) ? fallback : parsed
}

export function collectLegendItems(option: EChartOption): string[] {
  const names = new Set<string>()
  const series = option.series

  if (!Array.isArray(series)) return []

  for (const raw of series) {
    const entry = raw as {
      name?: string
      type?: string
      data?: { name?: string }[]
    }

    if (entry.name) names.add(entry.name)

    if (entry.type === 'pie' && Array.isArray(entry.data)) {
      for (const point of entry.data) {
        if (point?.name) names.add(point.name)
      }
    }
  }

  return [...names]
}

/** Estimate wrapped legend rows for a ~900px-wide analytics chart. */
export function estimateLegendRows(items: string[]): number {
  if (!items.length) return 0
  if (items.length === 1) return 1

  const avgLabelLength = items.reduce((sum, name) => sum + name.length, 0) / items.length
  const estimatedItemWidth = 12 + 10 + avgLabelLength * 6.5 + 14
  const containerWidth = 820
  const itemsPerRow = Math.max(1, Math.floor((containerWidth * 0.96) / estimatedItemWidth))

  return Math.ceil(items.length / itemsPerRow)
}

export function buildChartLegendLayout(option: EChartOption): ChartLegendLayout | null {
  const items = collectLegendItems(option)
  if (!items.length) return null

  const itemCount = items.length
  const rows = estimateLegendRows(items)
  const useScroll = itemCount > 16
  const compact = itemCount > 10

  const legend: Record<string, unknown> = {
    show: true,
    type: useScroll ? 'scroll' : 'plain',
    orient: 'horizontal',
    bottom: 10,
    left: 'center',
    width: '96%',
    itemGap: compact ? 12 : 16,
    itemWidth: 14,
    itemHeight: 10,
    textStyle: {
      fontFamily: CHART_FONT_FAMILY,
      fontSize: compact ? 11 : 12,
      // Keep full Khmer/English labels visible (no ellipsis).
      overflow: 'break',
    },
    tooltip: { show: true },
    ...(useScroll
      ? {
          pageButtonItemGap: 6,
          pageIconSize: 10,
          pageTextStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 11 },
        }
      : {}),
  }

  const rowHeightPercent = 4.2
  const gridBottom = `${Math.min(10 + rows * rowHeightPercent + (useScroll ? 2 : 0), 28)}%`
  const pieLiftPercent = Math.min(2 + (rows - 1) * 2.2 + (itemCount > 8 ? 2 : 0), 16)

  return {
    itemCount,
    rows,
    legend,
    gridBottom,
    pieLiftPercent,
  }
}

export function applyLegendLayoutToOption(
  option: EChartOption,
  layout: ChartLegendLayout,
): EChartOption {
  const next: EChartOption = { ...option }

  if (Array.isArray(next.series)) {
    next.series = next.series.map((raw) => {
      const series = { ...(raw as Record<string, unknown>) }
      if (series.type !== 'pie' || !Array.isArray(series.center)) return series

      const center = series.center as [unknown, unknown]
      const currentY = parsePercent(center[1], 50)
      const nextY = Math.max(24, currentY - layout.pieLiftPercent)

      series.center = [center[0], `${nextY}%`]

      if (layout.itemCount > 10 && typeof series.radius === 'string' && series.radius.endsWith('%')) {
        const radius = parsePercent(series.radius, 55)
        series.radius = `${Math.max(radius - 3, 36)}%`
      }

      if (Array.isArray(series.radius)) {
        series.radius = series.radius.map((value) => {
          if (typeof value === 'string' && value.endsWith('%')) {
            return `${Math.max(parsePercent(value, 40) - 2, 30)}%`
          }
          return value
        })
      }

      if (layout.itemCount > 12) {
        series.label = {
          ...(series.label as object || {}),
          show: false,
        }
        series.labelLine = {
          ...(series.labelLine as object || {}),
          show: false,
        }
      }

      return series
    })
  }

  return next
}

export function resolveGridBottomWithLegend(
  existingBottom: unknown,
  layout: ChartLegendLayout,
  hasGrid: boolean,
): number | string {
  if (!hasGrid) {
    if (typeof existingBottom === 'number' || typeof existingBottom === 'string') {
      return existingBottom
    }
    return '4%'
  }

  const layoutValue = parsePercent(layout.gridBottom, 16)
  const existingValue = typeof existingBottom === 'string' && String(existingBottom).endsWith('%')
    ? parsePercent(existingBottom, 0)
    : 0

  if (existingValue > 0) {
    return `${Math.max(existingValue, layoutValue)}%`
  }

  return layout.gridBottom
}

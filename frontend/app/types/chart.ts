export type ChartKind =
  | 'smoothLine'
  | 'dualAxisMixed'
  | 'signedHorizontalBar'
  | 'shareDataset'
  | 'scrollLegendPie'
  | 'halfDonut'
  | 'waterfall'
  | 'comboBarLine'
  | 'rosePie'
  | 'donut'
  | 'pie'
  | 'horizontalBar'
  | 'lineMarkLine'
  | 'groupedBar'
  | 'stackedBar'
  | 'verticalBar'

export interface ChartSeriesPoint {
  name: string
  value: number
}

export interface ChartLineSeriesData {
  labels: string[]
  values: number[]
  seriesName?: string
  color?: string
}

export interface ChartDualAxisMixedData {
  labels: string[]
  series: {
    type: 'bar' | 'line'
    name: string
    data: number[]
    color?: string
    yAxisIndex?: number
  }[]
  yAxisNames?: [string?, string?]
}

export interface ChartSignedHorizontalBarData {
  categories: string[]
  series: {
    name: string
    data: number[]
    color?: string
  }[]
}

export interface ChartShareDatasetData {
  items: ChartSeriesPoint[]
  trends: {
    name: string
    labels: string[]
    values: number[]
    color?: string
  }[]
}

export interface ChartWaterfallData {
  labels: string[]
  steps: {
    name: string
    value: number
    color?: string
  }[]
}

export interface ChartComboBarLineData {
  labels: string[]
  barValues: number[]
  lineValues: number[]
  barName: string
  lineName: string
  barColor?: string
  lineColor?: string
}

export interface ChartLineMarkData {
  labels: string[]
  values: number[]
  seriesName: string
  markLineValue: number
  markLineLabel: string
  color?: string
}

export interface ChartGroupedBarData {
  categories: string[]
  series: { name: string; data: number[]; color?: string }[]
}

export type BuiltChartData =
  | ChartSeriesPoint[]
  | ChartLineSeriesData
  | ChartDualAxisMixedData
  | ChartSignedHorizontalBarData
  | ChartShareDatasetData
  | ChartWaterfallData
  | ChartComboBarLineData
  | ChartLineMarkData
  | ChartGroupedBarData

/** Dashboard home page stat cards. */
export interface Statistic {
  label: string
  value: string
  icon: string
}

interface ChartDataPoint {
  name: string
  value: number
}

export interface NestedPieGroup {
  name: string
  children: ChartDataPoint[]
}

export interface ComboChartData {
  labels: string[]
  barValues: number[]
  lineValues: number[]
  barLabel?: string
  lineLabel?: string
}

/** Dashboard / analytics API payload (home index + modal analytics). */
export interface PageAnalytics {
  stats: Statistic[]
  chartData: ChartDataPoint[]
  lineData?: { labels: string[]; values: number[]; barValues?: number[] }
  /** Bar + line dual-axis chart for monthly quick view. */
  monthlyComboData?: ComboChartData
  mapData?: ChartDataPoint[]
  /** Province-style stacked horizontal bar when API provides it; otherwise derived from mapData. */
  stackedBarData?: { labels: string[]; datasets: { name: string; values: number[] }[] }
  /** Right-column status summary; otherwise derived from stats. */
  summaryList?: { label: string; value: string }[]
  /** Nested inner/outer pie for module distribution dashboard card. */
  moduleDistribution?: NestedPieGroup[]
}

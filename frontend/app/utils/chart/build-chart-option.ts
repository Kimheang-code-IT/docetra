import type { ChartKind } from '~/types/chart'
import {
  comboBarLineOption,
  donutOption,
  dualAxisMixedOption,
  groupedBarOption,
  halfDonutOption,
  horizontalBarOption,
  lineWithMarkLineOption,
  pieOption,
  rosePieOption,
  scrollLegendPieOption,
  shareDatasetOption,
  signedHorizontalBarOption,
  smoothLineOption,
  stackedBarOption,
  verticalBarOption,
  waterfallOption,
} from '~/utils/chart/echart-options'

type TranslateFn = (key: string, params?: Record<string, unknown>) => string

export function buildChartOption(
  kind: ChartKind,
  data: unknown,
  t: TranslateFn,
): Record<string, unknown> | null {
  if (!data) return null

  switch (kind) {
    case 'smoothLine': {
      const payload = data as { labels: string[]; values: number[]; seriesName?: string; color?: string }
      return smoothLineOption(payload.labels, payload.values, payload.seriesName, payload.color)
    }
    case 'dualAxisMixed': {
      const payload = data as {
        labels: string[]
        series: { type: 'bar' | 'line'; name: string; data: number[]; color?: string; yAxisIndex?: number }[]
        yAxisNames?: [string?, string?]
      }
      return dualAxisMixedOption(payload.labels, payload.series, payload.yAxisNames)
    }
    case 'signedHorizontalBar': {
      const payload = data as { categories: string[]; series: { name: string; data: number[]; color?: string }[] }
      return signedHorizontalBarOption(payload.categories, payload.series)
    }
    case 'shareDataset': {
      const payload = data as {
        items: { name: string; value: number }[]
        trends: { name: string; labels: string[]; values: number[]; color?: string }[]
      }
      return shareDatasetOption(payload.items, payload.trends)
    }
    case 'scrollLegendPie':
      return scrollLegendPieOption(data as { name: string; value: number }[])
    case 'halfDonut':
      return halfDonutOption(data as { name: string; value: number }[])
    case 'waterfall': {
      const payload = data as { labels: string[]; steps: { name: string; value: number; color?: string }[] }
      return waterfallOption(payload.labels, payload.steps)
    }
    case 'comboBarLine': {
      const payload = data as {
        labels: string[]
        barValues: number[]
        lineValues: number[]
        barName: string
        lineName: string
        barColor?: string
        lineColor?: string
      }
      return comboBarLineOption(
        payload.labels,
        payload.barValues,
        payload.lineValues,
        payload.barName,
        payload.lineName,
        payload.barColor,
        payload.lineColor,
      )
    }
    case 'rosePie':
      return rosePieOption(data as { name: string; value: number }[])
    case 'donut':
      return donutOption(data as { name: string; value: number }[])
    case 'pie':
      return pieOption(data as { name: string; value: number }[])
    case 'horizontalBar': {
      const payload = data as { items: { name: string; value: number }[]; color?: string; seriesName?: string }
      return horizontalBarOption(payload.items, payload.color, payload.seriesName)
    }
    case 'lineMarkLine': {
      const payload = data as {
        labels: string[]
        values: number[]
        seriesName: string
        markLineValue: number
        markLineLabel: string
        color?: string
      }
      return lineWithMarkLineOption(
        payload.labels,
        payload.values,
        payload.seriesName,
        payload.markLineValue,
        payload.markLineLabel,
        payload.color,
      )
    }
    case 'groupedBar': {
      const payload = data as { categories: string[]; series: { name: string; data: number[]; color?: string }[] }
      return groupedBarOption(payload.categories, payload.series)
    }
    case 'stackedBar': {
      const payload = data as { categories: string[]; series: { name: string; data: number[]; color?: string }[] }
      return stackedBarOption(payload.categories, payload.series)
    }
    case 'verticalBar': {
      const payload = data as { labels: string[]; values: number[]; color?: string; seriesName?: string }
      return verticalBarOption(payload.labels, payload.values, payload.color, payload.seriesName)
    }
    default:
      return null
  }
}

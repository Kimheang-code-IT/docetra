import { shouldDisableChartAnimation } from '~/composables/chart/useReactiveChartData'
import {
  applyLegendLayoutToOption,
  buildChartLegendLayout,
  collectLegendItems,
  resolveGridBottomWithLegend,
} from '~/utils/chart/chart-legend-layout'

export const CHART_FONT_FAMILY = '"Noto Sans Khmer", "Khmer OS Siemreap", "Inter", sans-serif'

export type ChartChromeMeta = {
  title?: string
  downloadTitle?: string
  dark?: boolean
}

export function chartPalette(dark = false) {
  return {
    backgroundColor: dark ? '#18191a' : '#ffffff',
    text: dark ? '#a1a1aa' : '#64748b',
    axis: dark ? '#71717a' : '#94a3b8',
    split: dark ? '#3f3f46' : '#f1f5f9',
    axisLine: dark ? '#3f3f46' : '#e2e8f0',
    title: dark ? '#f4f4f5' : '#0f172a',
  }
}

type EChartOption = Record<string, unknown>

function axisWithFont(axis: unknown, palette?: ReturnType<typeof chartPalette>) {
  if (!axis) return axis
  const apply = (item: Record<string, unknown>) => {
    const next: Record<string, unknown> = {
      ...item,
      nameTextStyle: {
        fontFamily: CHART_FONT_FAMILY,
        ...(palette ? { color: palette.text } : {}),
        ...(item.nameTextStyle as object || {}),
      },
      axisLabel: {
        fontFamily: CHART_FONT_FAMILY,
        ...(palette ? { color: palette.text } : {}),
        ...(item.axisLabel as object || {}),
      },
    }

    if (palette) {
      const axisLine = (item.axisLine as { lineStyle?: Record<string, unknown> }) || {}
      const splitLine = (item.splitLine as { lineStyle?: Record<string, unknown> }) || {}
      next.axisLine = {
        ...axisLine,
        lineStyle: {
          color: palette.axisLine,
          ...(axisLine.lineStyle || {}),
        },
      }
      next.splitLine = {
        ...splitLine,
        lineStyle: {
          ...(splitLine.lineStyle || {}),
          color: palette.split,
        },
      }
    }

    return next
  }
  if (Array.isArray(axis)) return axis.map((item) => apply(item as Record<string, unknown>))
  return apply(axis as Record<string, unknown>)
}

function hasNamedSeries(option: EChartOption) {
  const series = option.series
  if (!Array.isArray(series)) return false
  return series.some((item) => Boolean((item as { name?: string }).name))
}

function hasPieData(option: EChartOption) {
  const series = option.series
  if (!Array.isArray(series)) return false
  return series.some((item) => {
    const entry = item as { type?: string; data?: unknown[] }
    return entry.type === 'pie' && Array.isArray(entry.data) && entry.data.length > 0
  })
}

export function bottomLegendOption(overrides: Record<string, unknown> = {}) {
  return {
    show: true,
    type: 'plain',
    orient: 'horizontal',
    bottom: 4,
    left: 'center',
    width: '96%',
    itemGap: 14,
    itemWidth: 10,
    itemHeight: 8,
    textStyle: {
      fontFamily: CHART_FONT_FAMILY,
      fontSize: 12,
    },
    ...overrides,
  }
}

export function withChartChrome(option: EChartOption | null, meta?: ChartChromeMeta) {
  if (!option) return null

  const legendItems = collectLegendItems(option)
  const showLegend = legendItems.length > 0 || hasNamedSeries(option) || hasPieData(option)
  const legendLayout = showLegend ? buildChartLegendLayout(option) : null
  const hasTitle = Boolean(meta?.title)
  const isDualAxis = Array.isArray(option.yAxis) && (option.yAxis as unknown[]).length > 1
  const topOffset = hasTitle ? 44 : (isDualAxis ? 16 : 12)
  const optionGrid = option.grid as Record<string, unknown> | undefined
  const hasGrid = Boolean(optionGrid || option.xAxis)

  let prepared = legendLayout ? applyLegendLayoutToOption(option, legendLayout) : option
  const palette = chartPalette(Boolean(meta?.dark))

  const merged: EChartOption = {
    ...prepared,
    backgroundColor: prepared.backgroundColor ?? palette.backgroundColor,
    textStyle: {
      fontFamily: CHART_FONT_FAMILY,
      color: palette.text,
      ...(prepared.textStyle as object || {}),
    },
    tooltip: {
      ...(prepared.tooltip as object || {}),
      textStyle: {
        fontFamily: CHART_FONT_FAMILY,
        ...((prepared.tooltip as { textStyle?: object })?.textStyle || {}),
      },
    },
    toolbox: {
      show: false,
      feature: {
        saveAsImage: {
          show: true,
          title: meta?.downloadTitle || 'Download',
          pixelRatio: 2,
          excludeComponents: [],
        },
      },
    },
    grid: hasGrid
      ? {
          left: isDualAxis ? '3%' : '2%',
          right: isDualAxis ? '4%' : '2%',
          containLabel: true,
          ...(optionGrid || {}),
          top: hasTitle ? topOffset : (optionGrid?.top ?? topOffset),
          bottom: legendLayout
            ? resolveGridBottomWithLegend(optionGrid?.bottom, legendLayout, true)
            : (optionGrid?.bottom ?? '4%'),
        }
      : prepared.grid,
  }

  if (hasTitle) {
    merged.title = {
      text: meta?.title,
      left: 'center',
      top: 8,
      textStyle: {
        fontFamily: CHART_FONT_FAMILY,
        fontSize: 14,
        fontWeight: 600,
        color: palette.title,
      },
    }

    // Keep pie series below the chart title
    if (Array.isArray(merged.series)) {
      merged.series = merged.series.map((raw) => {
        const series = { ...(raw as Record<string, unknown>) }
        if (series.type !== 'pie' || !Array.isArray(series.center)) return series
        const center = series.center as [unknown, unknown]
        const currentY = typeof center[1] === 'string' && center[1].endsWith('%')
          ? Number.parseFloat(center[1])
          : Number(center[1]) || 50
        series.center = [center[0], `${Math.min(currentY + 4, 58)}%`]
        return series
      })
    }
  }

  if (showLegend && legendLayout) {
    const preparedLegend = (prepared.legend as Record<string, unknown>) || {}
    const layoutLegend = legendLayout.legend
    const { top: _ignoredTop, ...preparedLegendRest } = preparedLegend

    merged.legend = {
      ...preparedLegendRest,
      ...layoutLegend,
      top: undefined,
      bottom: (layoutLegend.bottom as number | string | undefined) ?? 10,
      textStyle: {
        ...(layoutLegend.textStyle as object || {}),
        color: palette.text,
        ...((preparedLegend.textStyle as object) || {}),
      },
      show: true,
    }
  } else if (prepared.legend) {
    const preparedLegend = prepared.legend as Record<string, unknown>
    merged.legend = {
      ...preparedLegend,
      textStyle: {
        color: palette.text,
        fontFamily: CHART_FONT_FAMILY,
        ...((preparedLegend.textStyle as object) || {}),
      },
      show: true,
    }
  }

  if (merged.xAxis) merged.xAxis = axisWithFont(merged.xAxis, palette)
  if (merged.yAxis) merged.yAxis = axisWithFont(merged.yAxis, palette)

  return merged
}

export function baseCartesianOption() {
  return {
    tooltip: { trigger: 'axis' },
    grid: { left: '2%', right: '2%', bottom: '4%', containLabel: true },
  }
}

export function smoothLineOption(
  labels: string[],
  values: number[],
  seriesName?: string,
  color = '#2563eb',
  options: { area?: boolean; smooth?: boolean } = {},
) {
  if (!labels.length) return null
  const { area = true, smooth = true } = options
  return {
    animation: !shouldDisableChartAnimation(labels.length),
    ...baseCartesianOption(),
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLabel: { rotate: labels.length > 6 ? 24 : 0 },
    },
    yAxis: {
      type: 'value',
    },
    series: [{
      type: 'line',
      name: seriesName,
      smooth,
      data: values,
      showSymbol: labels.length <= 24,
      symbolSize: 6,
      lineStyle: { width: 2, color },
      itemStyle: { color },
      areaStyle: area ? { opacity: 0.12, color } : undefined,
    }],
  }
}

export function multiLineOption(
  labels: string[],
  series: { name: string; data: number[]; color?: string }[],
) {
  if (!labels.length || !series.length) return null
  return {
    animation: !shouldDisableChartAnimation(labels.length * series.length),
    ...baseCartesianOption(),
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLabel: { rotate: labels.length > 6 ? 24 : 0 },
    },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: series.map((s) => ({
      type: 'line',
      name: s.name,
      smooth: true,
      data: s.data,
      showSymbol: labels.length <= 18,
      symbolSize: 6,
      lineStyle: { width: 2, color: s.color },
      itemStyle: { color: s.color },
    })),
  }
}

export function rosePieOption(items: { name: string; value: number }[]) {
  if (!items.length) return null
  const palette = ['#2563eb', '#16a34a', '#f59e0b', '#7c3aed', '#0d9488', '#dc2626', '#0891b2', '#ea580c']
  return {
    animation: !shouldDisableChartAnimation(items.length),
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['18%', '68%'],
      center: ['50%', '55%'],
      roseType: 'area',
      itemStyle: { borderRadius: 4 },
      data: items.map((item, index) => ({
        ...item,
        itemStyle: { color: palette[index % palette.length] },
      })),
    }],
  }
}

export function lineWithMarkLineOption(
  labels: string[],
  values: number[],
  seriesName: string,
  markLineValue: number,
  markLineLabel: string,
  color = '#f59e0b',
) {
  if (!labels.length) return null
  const maxVal = Math.max(...values, markLineValue, 0)
  return {
    animation: !shouldDisableChartAnimation(labels.length),
    ...baseCartesianOption(),
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLabel: { rotate: labels.length > 6 ? 28 : 0, interval: 0 },
    },
    yAxis: { type: 'value', max: Math.ceil(maxVal * 1.15) || markLineValue },
    series: [{
      type: 'line',
      name: seriesName,
      smooth: true,
      data: values,
      symbolSize: 7,
      lineStyle: { width: 2, color },
      itemStyle: { color },
      markLine: {
        symbol: 'none',
        lineStyle: { color: '#dc2626', type: 'dashed' },
        label: { formatter: markLineLabel, fontFamily: CHART_FONT_FAMILY },
        data: [{ yAxis: markLineValue }],
      },
    }],
  }
}

export function verticalBarOption(
  labels: string[],
  values: number[],
  color = '#16a34a',
  seriesName?: string,
) {
  if (!labels.length) return null
  return {
    animation: !shouldDisableChartAnimation(labels.length),
    ...baseCartesianOption(),
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: labels.length > 6 ? 24 : 0 } },
    yAxis: { type: 'value' },
    series: [{
      type: 'bar',
      name: seriesName,
      data: values,
      itemStyle: { color, borderRadius: [4, 4, 0, 0] },
    }],
  }
}

export function horizontalBarOption(
  items: { name: string; value: number }[],
  color = '#2563eb',
  seriesName?: string,
) {
  if (!items.length) return null
  return {
    animation: !shouldDisableChartAnimation(items.length),
    ...baseCartesianOption(),
    xAxis: { type: 'value' },
    yAxis: { type: 'category', data: items.map((i) => i.name) },
    series: [{
      type: 'bar',
      name: seriesName,
      data: items.map((i) => i.value),
      itemStyle: { color },
    }],
  }
}

export function donutOption(items: { name: string; value: number }[]) {
  if (!items.length) return null
  return {
    animation: !shouldDisableChartAnimation(items.length),
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      data: items,
    }],
  }
}

export function pieOption(items: { name: string; value: number }[]) {
  if (!items.length) return null
  return {
    tooltip: { trigger: 'item' },
    series: [{ type: 'pie', radius: '65%', data: items }],
  }
}

export function stackedBarOption(
  categories: string[],
  series: { name: string; data: number[]; color?: string }[],
) {
  if (!categories.length || !series.length) return null
  return {
    animation: !shouldDisableChartAnimation(categories.length * series.length),
    ...baseCartesianOption(),
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value' },
    series: series.map((s) => ({
      type: 'bar',
      name: s.name,
      stack: 'total',
      data: s.data,
      itemStyle: s.color ? { color: s.color } : undefined,
    })),
  }
}

export function groupedBarOption(
  categories: string[],
  series: { name: string; data: number[]; color?: string }[],
) {
  if (!categories.length || !series.length) return null
  return {
    animation: !shouldDisableChartAnimation(categories.length * series.length),
    ...baseCartesianOption(),
    xAxis: { type: 'category', data: categories },
    yAxis: { type: 'value' },
    series: series.map((s) => ({
      type: 'bar',
      name: s.name,
      data: s.data,
      itemStyle: s.color ? { color: s.color } : undefined,
    })),
  }
}

export function comboBarLineOption(
  labels: string[],
  barValues: number[],
  lineValues: number[],
  barName: string,
  lineName: string,
  barColor = '#2563eb',
  lineColor = '#f59e0b',
) {
  if (!labels.length) return null
  return {
    animation: !shouldDisableChartAnimation(labels.length),
    ...baseCartesianOption(),
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: labels.length > 6 ? 24 : 0 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: [
      {
        type: 'bar',
        name: barName,
        data: barValues,
        itemStyle: { color: barColor, borderRadius: [4, 4, 0, 0] },
        barMaxWidth: 40,
      },
      {
        type: 'line',
        name: lineName,
        smooth: true,
        data: lineValues,
        symbolSize: 7,
        lineStyle: { width: 2, color: lineColor },
        itemStyle: { color: lineColor },
      },
    ],
  }
}

export const CHART_PALETTE = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']

export function dualAxisMixedOption(
  labels: string[],
  series: {
    type: 'bar' | 'line'
    name: string
    data: number[]
    color?: string
    yAxisIndex?: number
  }[],
  yAxisNames: [string?, string?] = [],
) {
  if (!labels.length || !series.length) return null
  const useDualAxis = series.some((s) => s.yAxisIndex === 1)
  const fewCategories = labels.length <= 4

  return {
    animation: !shouldDisableChartAnimation(labels.length * series.length),
    ...baseCartesianOption(),
    // Leave room for bottom legend; avoid side axis titles (Khmer overlaps) — legend carries series names.
    grid: {
      left: useDualAxis ? '4%' : '3%',
      right: useDualAxis ? '5%' : '3%',
      top: '8%',
      bottom: '18%',
      containLabel: true,
    },
    legend: {
      show: true,
      type: 'plain',
      orient: 'horizontal',
      bottom: 8,
      left: 'center',
      data: series.map((s) => s.name).filter(Boolean),
    },
    tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
    xAxis: {
      type: 'category',
      data: labels,
      axisLabel: { rotate: labels.length > 6 ? 24 : 0 },
      axisPointer: { type: 'shadow' },
    },
    yAxis: useDualAxis
      ? [
          {
            type: 'value',
            // Keep axis clean; series names belong in the legend.
            name: undefined,
            scale: true,
            alignTicks: true,
            splitLine: { lineStyle: { color: '#f1f5f9' } },
            axisLabel: { hideOverlap: true },
          },
          {
            type: 'value',
            name: undefined,
            scale: true,
            alignTicks: true,
            splitLine: { show: false },
            axisLabel: { hideOverlap: true },
          },
        ]
      : [{
          type: 'value',
          name: yAxisNames[0],
          nameLocation: 'end',
          nameGap: 8,
          nameTextStyle: { fontSize: 11, overflow: 'truncate', width: 100 },
          splitLine: { lineStyle: { color: '#f1f5f9' } },
          axisLabel: { hideOverlap: true },
        }],
    series: series.map((s, index) => ({
      type: s.type,
      name: s.name,
      yAxisIndex: s.yAxisIndex ?? 0,
      data: s.data,
      smooth: s.type === 'line',
      showSymbol: s.type === 'line',
      symbolSize: s.type === 'line' ? 8 : undefined,
      barMaxWidth: s.type === 'bar' ? (fewCategories ? 72 : 36) : undefined,
      barMinWidth: s.type === 'bar' && fewCategories ? 28 : undefined,
      itemStyle: {
        color: s.color ?? CHART_PALETTE[index % CHART_PALETTE.length],
        borderRadius: s.type === 'bar' ? [4, 4, 0, 0] : undefined,
      },
      lineStyle: s.type === 'line'
        ? { width: 2.5, color: s.color ?? CHART_PALETTE[index % CHART_PALETTE.length] }
        : undefined,
    })),
  }
}

export function signedHorizontalBarOption(
  categories: string[],
  series: { name: string; data: number[]; color?: string }[],
) {
  if (!categories.length || !series.length) return null
  return {
    animation: !shouldDisableChartAnimation(categories.length * series.length),
    tooltip: { trigger: 'axis', axisPointer: { type: 'shadow' } },
    grid: { left: '3%', right: '4%', bottom: '16%', containLabel: true },
    xAxis: { type: 'value', splitLine: { lineStyle: { color: '#f1f5f9' } } },
    yAxis: { type: 'category', data: categories, axisTick: { show: false } },
    series: series.map((s, index) => ({
      type: 'bar',
      name: s.name,
      stack: series.length > 1 ? 'total' : undefined,
      label: { show: true, position: 'right', fontFamily: CHART_FONT_FAMILY },
      emphasis: { focus: 'series' },
      data: s.data,
      itemStyle: { color: s.color ?? CHART_PALETTE[index % CHART_PALETTE.length] },
    })),
  }
}

export function shareDatasetOption(
  items: { name: string; value: number }[],
  trends: { name: string; labels: string[]; values: number[]; color?: string }[],
) {
  if (!items.length || !trends.length) return null
  const palette = CHART_PALETTE
  return {
    animation: !shouldDisableChartAnimation(items.length + trends.length),
    tooltip: { trigger: 'item' },
    grid: { left: '3%', right: '4%', top: '52%', bottom: '18%', containLabel: true },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: trends[0]?.labels ?? [],
      axisLabel: { rotate: (trends[0]?.labels.length ?? 0) > 6 ? 24 : 0 },
    },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: [
      {
        type: 'pie',
        radius: '28%',
        center: ['50%', '26%'],
        label: { formatter: '{b}: {d}%' },
        data: items.map((item, index) => ({
          ...item,
          itemStyle: { color: palette[index % palette.length] },
        })),
      },
      ...trends.map((trend, index) => ({
        type: 'line',
        name: trend.name,
        smooth: true,
        showSymbol: trend.labels.length <= 18,
        data: trend.values,
        itemStyle: { color: trend.color ?? palette[index % palette.length] },
        lineStyle: { width: 2, color: trend.color ?? palette[index % palette.length] },
      })),
    ],
  }
}

export function scrollLegendPieOption(items: { name: string; value: number }[]) {
  if (!items.length) return null
  const palette = CHART_PALETTE
  return {
    animation: !shouldDisableChartAnimation(items.length),
    tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
    series: [{
      type: 'pie',
      radius: '58%',
      center: ['50%', '46%'],
      label: { show: items.length <= 12, fontFamily: CHART_FONT_FAMILY },
      labelLine: { show: items.length <= 12 },
      data: items.map((item, index) => ({
        ...item,
        itemStyle: { color: palette[index % palette.length] },
      })),
    }],
  }
}

export function halfDonutOption(items: { name: string; value: number }[]) {
  if (!items.length) return null
  const palette = CHART_PALETTE
  return {
    animation: !shouldDisableChartAnimation(items.length),
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: ['42%', '72%'],
      center: ['50%', '62%'],
      startAngle: 180,
      endAngle: 360,
      label: { show: true, fontFamily: CHART_FONT_FAMILY },
      data: items.map((item, index) => ({
        ...item,
        itemStyle: { color: palette[index % palette.length] },
      })),
    }],
  }
}

export function waterfallOption(
  labels: string[],
  steps: { name: string; value: number; color?: string }[],
) {
  if (!labels.length || !steps.length) return null
  let total = 0
  const placeholders: number[] = []
  const values: number[] = []
  const colors: string[] = []

  for (const step of steps) {
    if (step.value >= 0) {
      placeholders.push(total)
      values.push(step.value)
      total += step.value
    } else {
      total += step.value
      placeholders.push(total)
      values.push(Math.abs(step.value))
    }
    colors.push(step.color ?? (step.value >= 0 ? '#5470c6' : '#91cc75'))
  }

  return {
    animation: !shouldDisableChartAnimation(labels.length),
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      formatter: (params: unknown) => {
        const items = Array.isArray(params) ? params : [params]
        const valueItem = items.find((p) => (p as { seriesName?: string }).seriesName === 'value')
        const idx = (valueItem as { dataIndex?: number })?.dataIndex ?? 0
        const raw = steps[idx]?.value ?? 0
        return `${steps[idx]?.name ?? ''}: ${raw}`
      },
    },
    grid: { left: '3%', right: '4%', bottom: '16%', containLabel: true },
    xAxis: { type: 'category', data: labels, axisLabel: { rotate: labels.length > 8 ? 24 : 0 } },
    yAxis: { type: 'value', splitLine: { lineStyle: { color: '#f1f5f9' } } },
    series: [
      {
        name: 'placeholder',
        type: 'bar',
        stack: 'waterfall',
        itemStyle: { borderColor: 'transparent', color: 'transparent' },
        emphasis: { itemStyle: { borderColor: 'transparent', color: 'transparent' } },
        data: placeholders,
      },
      {
        name: 'value',
        type: 'bar',
        stack: 'waterfall',
        label: { show: true, position: 'top', fontFamily: CHART_FONT_FAMILY },
        data: values.map((value, index) => ({
          value,
          itemStyle: { color: colors[index] },
        })),
      },
    ],
  }
}

export function sumBy<T>(rows: T[], pick: (row: T) => number) {
  return rows.reduce((sum, row) => sum + (Number(pick(row)) || 0), 0)
}

export function aggregateMap<T>(
  rows: T[],
  keyFn: (row: T) => string,
  valueFn: (row: T) => number,
) {
  const map = new Map<string, number>()
  for (const row of rows) {
    const key = keyFn(row)
    map.set(key, (map.get(key) || 0) + valueFn(row))
  }
  return map
}

export function topEntries(map: Map<string, number>, limit = 10) {
  return [...map.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name, value]) => ({ name, value: Math.round(value) }))
}

export function monthKeyFromDate(date: string | undefined) {
  const value = String(date || '').trim()
  if (/^\d{4}-\d{2}/.test(value)) return value.slice(0, 7)
  const dayMonthYear = value.match(/^(\d{1,2})\/(\d{1,2})\/(\d{4})/)
  if (dayMonthYear) {
    const [, , month, year] = dayMonthYear
    return `${year}-${String(month).padStart(2, '0')}`
  }
  const parsed = new Date(value)
  if (!Number.isNaN(parsed.getTime())) {
    return `${parsed.getFullYear()}-${String(parsed.getMonth() + 1).padStart(2, '0')}`
  }
  return 'Unknown'
}

export function yearFromDate(date: string | undefined) {
  const key = monthKeyFromDate(date)
  if (key === 'Unknown') return null
  return key.slice(0, 4)
}

export function monthFromDate(date: string | undefined) {
  const key = monthKeyFromDate(date)
  if (key === 'Unknown') return null
  return key.slice(5, 7)
}

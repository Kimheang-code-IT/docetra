import type { ChartKind } from '~/types/chart'

export interface PageKpi {
  id: string
  label: string
  value: string
  icon?: string
}

export interface PageChartPanel {
  id: string
  title: string
  option: Record<string, unknown> | null
}

export interface PageChartDefinition<T = unknown> {
  id: string
  chartKind?: ChartKind
  title: (rows: T[], t: (key: string, params?: Record<string, unknown>) => string) => string
  subtitle?: (rows: T[], t: (key: string, params?: Record<string, unknown>) => string) => string
  build: (rows: T[]) => unknown | null
  toOption?: (data: unknown, t: (key: string, params?: Record<string, unknown>) => string) => Record<string, unknown> | null
}

export type AnyChartDefinition = PageChartDefinition<any>

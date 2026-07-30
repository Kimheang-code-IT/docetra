import type { ComputedRef, MaybeRefOrGetter } from 'vue'
import { computed, toValue } from 'vue'
import type { PageChartDefinition, PageChartPanel, PageKpi } from '~/types/page-chart'
import { buildChartOption } from '~/utils/chart/build-chart-option'

type TranslateFn = (key: string, params?: Record<string, unknown>) => string

export function usePageCharts<T>(
  source: MaybeRefOrGetter<T[]>,
  definitions: PageChartDefinition<T>[],
  kpisBuilder?: (rows: T[], t: TranslateFn) => PageKpi[],
): {
  definitions: PageChartDefinition<T>[]
  panels: ComputedRef<PageChartPanel[]>
  kpis: ComputedRef<PageKpi[]>
} {
  const { t } = useI18n()

  const rows = computed(() => toValue(source))

  const panels = computed<PageChartPanel[]>(() => {
    const data = rows.value
    return definitions.map((def) => {
      const built = data.length ? def.build(data) : null
      return {
        id: def.id,
        title: def.title(data, t),
        option: built
          ? (def.toOption?.(built, t) ?? (def.chartKind ? buildChartOption(def.chartKind, built, t) : null))
          : null,
      }
    })
  })

  const kpis = computed<PageKpi[]>(() => {
    if (!kpisBuilder) return []
    return kpisBuilder(rows.value, t)
  })

  return { definitions, panels, kpis }
}

<script setup lang="ts">
import { fetchDashboardSummary } from '~/adapters'
import { usePageSeo } from '~/composables/usePageSeo'
import type { DashboardSummary } from '~/types/docetra/entities'

definePageMeta({
  titleKey: 'docetra.pages.dashboard',
  permission: 'dashboard.view',
})

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

usePageSeo({
  title: () => t('docetra.pages.dashboard'),
})

const pending = ref(false)
const error = ref<string | null>(null)
const summary = ref<DashboardSummary | null>(null)

type DownloadableChart = {
  downloadChart: (filename?: string) => void
}

const stageChartRef = ref<DownloadableChart | null>(null)
const trendChartRef = ref<DownloadableChart | null>(null)

function downloadStageChart() {
  stageChartRef.value?.downloadChart('work-by-stage')
}

function downloadTrendChart() {
  trendChartRef.value?.downloadChart('records-over-time')
}

const chartYear = computed({
  get: () => String(route.query.chartYear || 'this'),
  set: (value: string) => {
    router.replace({
      query: {
        ...route.query,
        chartYear: !value || value === 'this' ? undefined : value,
      },
    })
  },
})

const chartPeriod = computed({
  get: () => String(route.query.chartPeriod || 'monthly'),
  set: (value: string) => {
    router.replace({
      query: {
        ...route.query,
        chartPeriod: !value || value === 'monthly' ? undefined : value,
      },
    })
  },
})

function resolveFilterYear(token: string) {
  const now = new Date().getFullYear()
  if (token === 'this') return now
  if (token === 'last') return now - 1
  const n = Number(token)
  return Number.isFinite(n) ? n : now
}

function monthKey(dateStr: string) {
  return dateStr.slice(0, 7)
}

function quarterKey(dateStr: string) {
  const [y, m] = dateStr.split('-').map(Number)
  const q = Math.ceil((m || 1) / 3)
  return `${y}-Q${q}`
}

function weekKey(dateStr: string) {
  const d = new Date(`${dateStr.slice(0, 10)}T12:00:00`)
  const tmp = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()))
  const day = tmp.getUTCDay() || 7
  tmp.setUTCDate(tmp.getUTCDate() + 4 - day)
  const yearStart = new Date(Date.UTC(tmp.getUTCFullYear(), 0, 1))
  const week = Math.ceil((((tmp.getTime() - yearStart.getTime()) / 86400000) + 1) / 7)
  return `${tmp.getUTCFullYear()}-W${String(week).padStart(2, '0')}`
}

const filteredTrendSeries = computed(() => {
  const year = resolveFilterYear(chartYear.value)
  const period = chartPeriod.value
  const points = (summary.value?.recordsOverTime || [])
    .filter(p => Number(p.date.slice(0, 4)) === year)

  if (period === 'yearly') {
    const total = points.reduce((sum, p) => sum + p.count, 0)
    return [{ label: String(year), count: total }]
  }

  const bucketKey = period === 'quarterly'
    ? quarterKey
    : period === 'weekly'
      ? weekKey
      : monthKey

  const buckets = new Map<string, number>()
  for (const point of points) {
    const key = bucketKey(point.date)
    buckets.set(key, (buckets.get(key) || 0) + point.count)
  }
  return [...buckets.entries()]
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([label, count]) => ({ label, count }))
})

async function load() {
  pending.value = true
  error.value = null
  try {
    const res = await fetchDashboardSummary() as { data: DashboardSummary }
    summary.value = res.data
  }
  catch (e: any) {
    error.value = e?.message || 'Failed to load dashboard'
  }
  finally {
    pending.value = false
  }
}

watch(() => route.query, load, { deep: true, immediate: true })

const stageChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 16, top: 24, bottom: 32 },
  xAxis: {
    type: 'category',
    data: (summary.value?.workByStage || []).map(s => s.stage),
  },
  yAxis: { type: 'value' },
  series: [{
    type: 'bar',
    data: (summary.value?.workByStage || []).map(s => s.count),
  }],
}))

const trendChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 16, top: 24, bottom: 32 },
  xAxis: {
    type: 'category',
    data: filteredTrendSeries.value.map(s => s.label),
  },
  yAxis: { type: 'value' },
  series: [{
    type: 'line',
    smooth: true,
    data: filteredTrendSeries.value.map(s => s.count),
    areaStyle: { opacity: 0.12 },
  }],
}))

const SUMMARY_CARD_LIMIT = 5

const summaryCards = computed(() => (summary.value?.kpis || []).slice(0, SUMMARY_CARD_LIMIT))
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-auto bg-muted/20">
    <LayoutAppHeaderPageActions
      :can-create="false"
      :refreshing="pending"
      @refresh="load"
    />

    <div class="relative flex w-full min-w-0 flex-1 flex-col gap-3 px-1.5 pt-1.5 pb-0">
      <UAlert v-if="error" color="error" :title="error" :actions="[{ label: $t('docetra.actions.retry'), onClick: load }]" />

      <template v-if="summary">
        <div class="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
          <CommonAppSummaryCard
            v-for="kpi in summaryCards"
            :key="kpi.id"
            :title="$t(kpi.labelKey)"
            :value="kpi.value"
            :trend="kpi.trend"
            :to="kpi.href"
            :loading="pending"
            @refresh="load"
          />
        </div>

        <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <section class="rounded-lg border border-default bg-default p-4">
            <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 class="text-sm font-semibold text-highlighted">{{ $t('docetra.dashboard.workByStage') }}</h2>
              <CommonAppChartPeriodToolbar
                v-model:year="chartYear"
                v-model:period="chartPeriod"
                @refresh="load"
                @download="downloadStageChart"
              />
            </div>
            <div class="h-64">
              <LazyCommonAppEchart ref="stageChartRef" :option="stageChartOption" height="100%" />
            </div>
          </section>
          <section class="rounded-lg border border-default bg-default p-4">
            <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
              <h2 class="text-sm font-semibold text-highlighted">{{ $t('docetra.dashboard.recordsOverTime') }}</h2>
              <CommonAppChartPeriodToolbar
                v-model:year="chartYear"
                v-model:period="chartPeriod"
                @refresh="load"
                @download="downloadTrendChart"
              />
            </div>
            <div class="h-64">
              <LazyCommonAppEchart ref="trendChartRef" :option="trendChartOption" height="100%" />
            </div>
          </section>
        </div>

        <LazyCommonAppEventCalendar :events="summary.events || []" />
      </template>
    </div>
  </div>
</template>

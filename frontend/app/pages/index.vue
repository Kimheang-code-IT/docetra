<script setup lang="ts">
import { CalendarDate, parseDate } from '@internationalized/date'
import { fetchDashboardSummary } from '~/adapters'
import type { DashboardSummary } from '~/types/docetra/entities'

definePageMeta({
  titleKey: 'docetra.pages.dashboard',
  permission: 'dashboard.view',
})

const { t } = useI18n()
const route = useRoute()
const router = useRouter()

useHead(() => ({
  title: `${t('docetra.pages.dashboard')} · ${t('docetra.brand.name')}`,
}))

const pending = ref(false)
const error = ref<string | null>(null)
const summary = ref<DashboardSummary | null>(null)

const dateRangeInput = useTemplateRef<{ inputsRef?: Array<{ $el?: HTMLElement }> } | null>('dateRangeInput')

function toCalendarDate(value?: string) {
  if (!value) return undefined
  try {
    return parseDate(value.slice(0, 10))
  }
  catch {
    return undefined
  }
}

const dateRange = computed({
  get: () => {
    const start = toCalendarDate(String(route.query.startDate || ''))
    const end = toCalendarDate(String(route.query.endDate || ''))
    if (!start && !end) return undefined
    return {
      start: start || end,
      end: end || start,
    }
  },
  set: (value: { start?: CalendarDate | null, end?: CalendarDate | null } | null | undefined) => {
    router.replace({
      query: {
        ...route.query,
        startDate: value?.start?.toString() || undefined,
        endDate: value?.end?.toString() || undefined,
      },
    })
  },
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
    data: (summary.value?.recordsOverTime || []).map(s => s.date),
  },
  yAxis: { type: 'value' },
  series: [{
    type: 'line',
    smooth: true,
    data: (summary.value?.recordsOverTime || []).map(s => s.count),
    areaStyle: { opacity: 0.12 },
  }],
}))

const quickLinks = [
  { to: '/records/incoming-documents', labelKey: 'docetra.pages.incomingDocument', icon: 'i-lucide-inbox' },
  { to: '/records/outgoing-documents', labelKey: 'docetra.pages.outgoingDocument', icon: 'i-lucide-send' },
  { to: '/meetings/topics', labelKey: 'docetra.pages.meetingTopic', icon: 'i-lucide-messages-square' },
  { to: '/portal/file-upload', labelKey: 'docetra.pages.fileUpload', icon: 'i-lucide-upload' },
]
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-auto bg-muted/20">
    <LayoutAppHeaderPageActions
      :can-create="false"
      :refreshing="pending"
      @refresh="load"
    >
      <template #leading>
        <UInputDate
          ref="dateRangeInput"
          v-model="dateRange"
          range
          color="neutral"
          variant="soft"
          size="sm"
          class="w-72"
        >
          <template #trailing>
            <UPopover :reference="dateRangeInput?.inputsRef?.[0]?.$el">
              <UButton
                color="neutral"
                variant="link"
                size="sm"
                icon="i-lucide-calendar"
                aria-label="Select a date range"
                class="px-0"
              />
              <template #content>
                <UCalendar v-model="dateRange" range :number-of-months="2" class="p-2" />
              </template>
            </UPopover>
          </template>
        </UInputDate>
      </template>
    </LayoutAppHeaderPageActions>

    <div class="relative flex w-full min-w-0 flex-1 flex-col gap-3 px-1.5 pt-1.5 pb-0">
      <div
        v-if="pending"
        class="absolute inset-x-1.5 top-1.5 bottom-0 z-10 flex items-start justify-center pt-24"
      >
        <UIcon name="i-lucide-loader-circle" class="size-6 animate-spin text-primary" />
      </div>

      <UAlert v-if="error" color="error" :title="error" :actions="[{ label: $t('docetra.actions.retry'), onClick: load }]" />

      <template v-if="summary">
        <p class="text-sm text-muted">{{ $t('docetra.descriptions.dashboard') }}</p>

        <div class="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-7">
          <NuxtLink
            v-for="kpi in summary.kpis || []"
            :key="kpi.id"
            :to="kpi.href || '/'"
            class="rounded-lg border border-default bg-default p-4 transition hover:border-primary/40"
          >
            <p class="text-xs text-muted">{{ $t(kpi.labelKey) }}</p>
            <p class="mt-2 text-2xl font-semibold text-highlighted">{{ kpi.value }}</p>
            <p v-if="kpi.trend != null" class="mt-1 text-xs" :class="kpi.trend >= 0 ? 'text-success' : 'text-error'">
              {{ kpi.trend >= 0 ? '+' : '' }}{{ kpi.trend }}%
            </p>
          </NuxtLink>
        </div>

        <div class="grid grid-cols-1 gap-4 xl:grid-cols-2">
          <section class="rounded-lg border border-default bg-default p-4">
            <h2 class="mb-3 text-sm font-semibold text-highlighted">{{ $t('docetra.dashboard.workByStage') }}</h2>
            <div class="h-64">
              <CommonAppEchart :option="stageChartOption" height="100%" />
            </div>
          </section>
          <section class="rounded-lg border border-default bg-default p-4">
            <h2 class="mb-3 text-sm font-semibold text-highlighted">{{ $t('docetra.dashboard.recordsOverTime') }}</h2>
            <div class="h-64">
              <CommonAppEchart :option="trendChartOption" height="100%" />
            </div>
          </section>
        </div>

        <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
          <section class="rounded-lg border border-default bg-default p-4 xl:col-span-2">
            <div class="mb-3 flex items-center justify-between">
              <h2 class="text-sm font-semibold text-highlighted">{{ $t('docetra.dashboard.myWork') }}</h2>
              <UButton size="xs" variant="link" to="/records/incoming-documents">{{ $t('docetra.actions.viewAll') }}</UButton>
            </div>
            <div class="overflow-x-auto">
              <table class="min-w-full text-sm">
                <thead>
                  <tr class="border-b border-default text-left text-muted">
                    <th class="px-2 py-2">{{ $t('docetra.fields.referenceNumber') }}</th>
                    <th class="px-2 py-2">{{ $t('docetra.fields.title') }}</th>
                    <th class="px-2 py-2">{{ $t('docetra.fields.stage') }}</th>
                    <th class="px-2 py-2">{{ $t('docetra.fields.status') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="row in summary.myWork || []"
                    :key="row.id"
                    class="cursor-pointer border-b border-default/70 hover:bg-elevated/50"
                    @click="navigateTo(`/records/incoming-documents/${row.id}`)"
                  >
                    <td class="px-2 py-2">{{ row.referenceNumber }}</td>
                    <td class="px-2 py-2">{{ row.title }}</td>
                    <td class="px-2 py-2"><UBadge color="neutral" variant="subtle">{{ row.stage }}</UBadge></td>
                    <td class="px-2 py-2">{{ row.status }}</td>
                  </tr>
                  <tr v-if="!(summary.myWork || []).length">
                    <td colspan="4" class="px-2 py-8 text-center text-muted">{{ $t('docetra.states.empty') }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section class="rounded-lg border border-default bg-default p-4 space-y-3">
            <h2 class="text-sm font-semibold text-highlighted">{{ $t('docetra.dashboard.quickLinks') }}</h2>
            <NuxtLink
              v-for="link in quickLinks"
              :key="link.to"
              :to="link.to"
              class="flex items-center gap-3 rounded-md border border-default px-3 py-2.5 transition hover:border-primary/40"
            >
              <UIcon :name="link.icon" class="size-4 text-primary" />
              <span class="text-sm text-highlighted">{{ $t(link.labelKey) }}</span>
            </NuxtLink>
          </section>
        </div>
      </template>
    </div>
  </div>
</template>

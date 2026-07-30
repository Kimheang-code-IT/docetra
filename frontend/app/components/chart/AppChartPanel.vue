<script setup lang="ts">
import type { AnyChartDefinition } from '~/types/page-chart'
import { buildChartOption } from '~/utils/chart/build-chart-option'
import { withChartChrome } from '~/utils/chart/echart-options'

const props = withDefaults(defineProps<{
  title?: string
  option?: Record<string, unknown> | null
  definition?: AnyChartDefinition
  sourceRows?: unknown[]
  getRowDate?: (row: unknown) => string | undefined
  loading?: boolean
  empty?: boolean
  emptyText?: string
  height?: string
  downloadFilename?: string
}>(), {
  loading: false,
  empty: false,
  height: '100%',
})

const { t } = useI18n()
const colorMode = useColorMode()
const chartRef = ref<{ downloadChart?: (filename: string) => void } | null>(null)

const isDefinitionMode = computed(() => Boolean(props.definition && props.sourceRows))

const resolvedTitle = computed(() => {
  if (props.title) return props.title
  if (props.definition) return props.definition.title((props.sourceRows ?? []) as never[], t)
  return ''
})

const resolvedBuilt = computed(() => {
  if (!isDefinitionMode.value || !props.definition) return null
  const data = props.sourceRows ?? []
  if (!data.length) return null
  return props.definition.build(data)
})

const resolvedOption = computed(() => {
  if (isDefinitionMode.value && props.definition) {
    const built = resolvedBuilt.value
    if (!built) return null
    if (props.definition.toOption) {
      return props.definition.toOption(built, t)
    }
    if (props.definition.chartKind) {
      return buildChartOption(props.definition.chartKind, built, t)
    }
    return null
  }
  return props.option ?? null
})

const isEmpty = computed(() => props.empty || !resolvedOption.value)

const enrichedOption = computed(() => withChartChrome(resolvedOption.value, {
  title: resolvedTitle.value || undefined,
  downloadTitle: t('components.downloadChart'),
  dark: colorMode.value === 'dark',
}))

const fillParent = computed(() => !props.height || props.height === '100%')

function downloadChart() {
  const filename = props.downloadFilename || resolvedTitle.value || 'chart'
  chartRef.value?.downloadChart?.(filename)
}

defineExpose({
  downloadChart,
  isEmpty,
})
</script>

<template>
  <div
    class="relative w-full min-h-0 flex flex-col"
    :class="fillParent ? 'flex-1 h-full' : ''"
    :style="fillParent ? undefined : { height, minHeight: height }"
  >
    <ChartAppChartSkeleton v-if="loading" :height="fillParent ? '100%' : height" />
    <div
      v-else-if="isEmpty"
      class="absolute inset-0 flex items-center justify-center text-xs text-muted-foreground px-4 text-center bg-default dark:bg-[#18191a]"
    >
      {{ emptyText || $t('common.noData') }}
    </div>
    <CommonAppEchart
      v-else
      ref="chartRef"
      :option="enrichedOption!"
      height="100%"
      class="absolute inset-0 w-full h-full"
    />
  </div>
</template>

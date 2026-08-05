<script setup lang="ts">
/**
 * ECharts wrapper — loads echarts only when the chart mounts (keeps first paint light).
 */
const props = withDefaults(defineProps<{
  option: Record<string, unknown>
  autoresize?: boolean
  width?: string | number
  height?: string | number
}>(), {
  autoresize: true,
  height: '100%',
})

const chartRef = ref<{
  getEchartsInstance?: () => { getDataURL: (opts: Record<string, unknown>) => string }
  chart?: { getDataURL: (opts: Record<string, unknown>) => string }
} | null>(null)

const VChart = shallowRef<Component | null>(null)
const ready = ref(false)

const chartStyle = computed(() => ({
  width: props.width
    ? (typeof props.width === 'number' ? `${props.width}px` : props.width)
    : '100%',
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  minHeight: 0,
}))

onMounted(async () => {
  const [
    { use },
    { CanvasRenderer },
    { LineChart, BarChart },
    {
      TooltipComponent,
      GridComponent,
    },
    { default: VueEcharts },
  ] = await Promise.all([
    import('echarts/core'),
    import('echarts/renderers'),
    import('echarts/charts'),
    import('echarts/components'),
    import('vue-echarts'),
  ])

  use([
    CanvasRenderer,
    LineChart,
    BarChart,
    TooltipComponent,
    GridComponent,
  ])

  VChart.value = VueEcharts as Component
  ready.value = true
})

function getInstance() {
  const el = chartRef.value
  if (!el) return null
  if (typeof el.getEchartsInstance === 'function') return el.getEchartsInstance()
  return el.chart ?? null
}

function downloadChart(filename = 'chart') {
  const instance = getInstance()
  if (!instance || typeof instance.getDataURL !== 'function') return

  const url = instance.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#ffffff',
  })

  const link = document.createElement('a')
  link.download = `${filename.replace(/[^\w\-]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '') || 'chart'}.png`
  link.href = url
  link.click()
}

defineExpose({ downloadChart })
</script>

<template>
  <div
    class="relative flex h-full min-h-0 w-full flex-col"
    :style="chartStyle"
  >
    <ClientOnly>
      <component
        :is="VChart"
        v-if="ready && VChart"
        ref="chartRef"
        :option="option"
        :autoresize="autoresize !== false"
        class="h-full min-h-0 w-full"
      />
      <div
        v-else
        class="flex h-full min-h-48 items-center justify-center"
      >
        <UIcon name="i-lucide-loader-circle" class="size-5 animate-spin text-muted" />
      </div>
    </ClientOnly>
  </div>
</template>

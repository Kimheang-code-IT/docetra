<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, LineChart, BarChart, MapChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  VisualMapComponent,
  GeoComponent,
  ToolboxComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  PieChart,
  LineChart,
  BarChart,
  MapChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
  DatasetComponent,
  VisualMapComponent,
  GeoComponent,
  ToolboxComponent,
])

const props = withDefaults(defineProps<{
  option: Record<string, unknown>
  autoresize?: boolean
  width?: string | number
  height?: string | number
}>(), {
  autoresize: true,
  height: '100%',
})

const chartRef = ref<InstanceType<typeof VChart> | null>(null)

const chartStyle = computed(() => ({
  width: props.width
    ? (typeof props.width === 'number' ? `${props.width}px` : props.width)
    : '100%',
  height: typeof props.height === 'number' ? `${props.height}px` : props.height,
  minHeight: 0,
}))

function getInstance() {
  const el = chartRef.value as {
    getEchartsInstance?: () => { getDataURL: (opts: Record<string, unknown>) => string }
    chart?: { getDataURL: (opts: Record<string, unknown>) => string }
  } | null
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
    class="relative flex flex-col w-full h-full min-h-0"
    :style="chartStyle"
  >
    <ClientOnly>
      <VChart
        ref="chartRef"
        :option="option"
        :autoresize="autoresize !== false"
        class="w-full h-full min-h-0"
      />
    </ClientOnly>
  </div>
</template>

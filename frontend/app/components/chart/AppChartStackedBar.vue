<script setup lang="ts">
import { bucketizeStackedData } from '~/utils/chart/optimizer'
import { CHART_FONT_FAMILY, chartPalette, withChartChrome } from '~/utils/chart/echart-options'

const props = defineProps<{
  data: {
    labels: string[]
    datasets: { name: string; values: number[] }[]
  }
  label?: string
}>()

const colorMode = useColorMode()
const optimized = computed(() => bucketizeStackedData(props.data, 140))
const isLarge = computed(() => props.data.labels.length > optimized.value.labels.length)

const option = computed(() => {
  const isDark = colorMode.value === 'dark'
  const palette = chartPalette(isDark)

  return withChartChrome({
    backgroundColor: palette.backgroundColor,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
    },
    animation: !isLarge.value,
    legend: {
      top: '1%',
      textStyle: { fontSize: 11, fontFamily: CHART_FONT_FAMILY, color: palette.text },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '8%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      axisLabel: { color: palette.text, fontFamily: CHART_FONT_FAMILY },
      splitLine: { lineStyle: { type: 'dashed', color: palette.split } },
    },
    yAxis: {
      type: 'category',
      data: optimized.value.labels,
      axisLine: { lineStyle: { color: palette.axisLine } },
      axisLabel: { color: palette.text, fontFamily: CHART_FONT_FAMILY },
    },
    series: optimized.value.datasets.map((ds, idx) => ({
      name: ds.name,
      type: 'bar',
      stack: 'total',
      label: { show: false, fontFamily: CHART_FONT_FAMILY },
      emphasis: { focus: 'series' },
      data: ds.values,
      large: true,
      largeThreshold: 800,
      progressive: 2000,
      progressiveThreshold: 3000,
      itemStyle: {
        borderRadius: idx === optimized.value.datasets.length - 1 ? [0, 4, 4, 0] : 0,
      },
    })),
  }, {
    title: props.label,
    dark: isDark,
  })
})
</script>

<template>
  <CommonAppEchart :option="option!" height="100%" />
</template>

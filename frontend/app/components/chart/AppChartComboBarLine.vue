<script setup lang="ts">
import type { ComboChartData } from '~/types/chart'
import { CHART_FONT_FAMILY, chartPalette, withChartChrome } from '~/utils/chart/echart-options'

const props = defineProps<{
  data: ComboChartData
  label?: string
}>()

const colorMode = useColorMode()

const topAxisLabels = computed(() =>
  props.data.labels.map((_, index) => String(index + 1)),
)

const option = computed(() => {
  const isDark = colorMode.value === 'dark'
  const palette = chartPalette(isDark)
  const barLabel = props.data.barLabel || 'Bar'
  const lineLabel = props.data.lineLabel || 'Line'
  const markerBorder = isDark ? '#18191a' : '#fff'

  return withChartChrome({
    backgroundColor: palette.backgroundColor,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
    },
    legend: {
      bottom: 8,
      left: 'center',
      textStyle: { fontFamily: CHART_FONT_FAMILY, fontSize: 12, color: palette.text },
    },
    grid: {
      left: '2%',
      right: '2%',
      top: '14%',
      bottom: '16%',
      containLabel: true,
    },
    xAxis: [
      {
        type: 'category',
        data: props.data.labels,
        axisPointer: { type: 'shadow' },
        axisLine: { lineStyle: { color: palette.axis } },
        axisLabel: { color: palette.text, fontSize: 11, fontFamily: CHART_FONT_FAMILY },
      },
      {
        type: 'category',
        position: 'top',
        data: topAxisLabels.value,
        axisLine: { show: false },
        axisTick: { show: false },
        axisLabel: { color: palette.text, fontSize: 11, fontFamily: CHART_FONT_FAMILY },
      },
    ],
    yAxis: [
      {
        type: 'value',
        name: lineLabel,
        nameLocation: 'end',
        nameTextStyle: {
          color: '#91cc75',
          fontSize: 11,
          fontFamily: CHART_FONT_FAMILY,
          padding: [0, 0, 4, 0],
        },
        position: 'left',
        axisLine: { show: true, lineStyle: { color: '#91cc75' } },
        axisLabel: { color: palette.text, fontSize: 11, fontFamily: CHART_FONT_FAMILY },
        splitLine: { lineStyle: { color: palette.split } },
      },
      {
        type: 'value',
        name: barLabel,
        nameLocation: 'end',
        nameTextStyle: {
          color: '#5470c6',
          fontSize: 11,
          fontFamily: CHART_FONT_FAMILY,
          padding: [0, 0, 4, 0],
        },
        position: 'right',
        axisLine: { show: true, lineStyle: { color: '#5470c6' } },
        axisLabel: { color: palette.text, fontSize: 11, fontFamily: CHART_FONT_FAMILY },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: barLabel,
        type: 'bar',
        yAxisIndex: 1,
        data: props.data.barValues,
        itemStyle: { color: '#5470c6' },
        barMaxWidth: 36,
      },
      {
        name: lineLabel,
        type: 'line',
        yAxisIndex: 0,
        data: props.data.lineValues,
        smooth: false,
        symbol: 'circle',
        symbolSize: 8,
        lineStyle: { color: '#91cc75', width: 2 },
        itemStyle: {
          color: '#91cc75',
          borderColor: markerBorder,
          borderWidth: 2,
        },
      },
    ],
  }, {
    // Card header already shows the section title — avoid duplicate overlay title
    dark: isDark,
  })
})
</script>

<template>
  <CommonAppEchart :option="option!" height="100%" />
</template>

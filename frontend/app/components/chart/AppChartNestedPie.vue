<script setup lang="ts">
import type { NestedPieGroup } from '~/types/chart'
import { nestedPieColors, nestedPieInnerData, nestedPieOuterData } from '~/utils/chart/nested-pie'
import { CHART_FONT_FAMILY, chartPalette, withChartChrome } from '~/utils/chart/echart-options'

const props = defineProps<{
  groups: NestedPieGroup[]
  label?: string
}>()

const colorMode = useColorMode()

const option = computed(() => {
  const isDark = colorMode.value === 'dark'
  const palette = chartPalette(isDark)
  const labelBg = isDark ? '#27272a' : '#F6F8FC'
  const labelBorder = isDark ? '#52525b' : '#8C8D8E'
  const badgeBg = isDark ? '#3f3f46' : '#4C5058'
  const title = props.label || ''

  const colors = nestedPieColors(props.groups)
  const innerData = nestedPieInnerData(props.groups, colors.inner)
  const outerData = nestedPieOuterData(props.groups, colors.outer)

  return withChartChrome({
    backgroundColor: palette.backgroundColor,
    tooltip: { trigger: 'item' },
    legend: {
      bottom: 0,
      left: 'center',
      type: 'scroll',
      textStyle: { color: palette.text, fontSize: 11, fontFamily: CHART_FONT_FAMILY },
    },
    series: [
      {
        name: title,
        type: 'pie',
        selectedMode: 'single',
        radius: [0, '28%'],
        center: ['50%', '48%'],
        label: {
          position: 'inner',
          fontSize: 11,
          fontFamily: CHART_FONT_FAMILY,
          color: '#fff',
          formatter: '{b}',
        },
        labelLine: { show: false },
        data: innerData,
      },
      {
        name: title,
        type: 'pie',
        radius: ['42%', '58%'],
        center: ['50%', '48%'],
        labelLine: {
          length: 18,
          length2: 14,
          smooth: true,
        },
        label: {
          alignTo: 'labelLine',
          fontFamily: CHART_FONT_FAMILY,
          formatter: (params: { name: string; value: number; percent: number }) =>
            `{title|${title}}\n{name|${params.name}: ${params.value} }{badge|${params.percent}%}`,
          backgroundColor: labelBg,
          borderColor: labelBorder,
          borderWidth: 1,
          borderRadius: 4,
          padding: [6, 10],
          rich: {
            title: {
              color: palette.text,
              fontSize: 10,
              fontFamily: CHART_FONT_FAMILY,
              lineHeight: 18,
              align: 'left',
            },
            name: {
              color: isDark ? '#e4e4e7' : '#333',
              fontSize: 11,
              fontFamily: CHART_FONT_FAMILY,
              lineHeight: 20,
              align: 'left',
            },
            badge: {
              color: '#fff',
              backgroundColor: badgeBg,
              padding: [2, 6],
              borderRadius: 4,
              fontSize: 10,
              fontFamily: CHART_FONT_FAMILY,
              lineHeight: 18,
            },
          },
        },
        data: outerData,
      },
    ],
  }, {
    title,
    dark: isDark,
  })
})
</script>

<template>
  <CommonAppEchart :option="option!" height="100%" />
</template>

export interface XYSeriesData {
  labels: string[]
  values: number[]
}

export interface StackedSeriesData {
  labels: string[]
  datasets: { name: string; values: number[] }[]
}

export interface PiePoint {
  name: string
  value: number
}

export function bucketizeSeries(data: XYSeriesData, maxPoints = 240): XYSeriesData {
  if (!data.labels.length || data.labels.length <= maxPoints) return data

  const bucketSize = Math.ceil(data.labels.length / maxPoints)
  const labels: string[] = []
  const values: number[] = []

  for (let i = 0; i < data.labels.length; i += bucketSize) {
    const end = Math.min(i + bucketSize, data.labels.length)
    const slice = data.values.slice(i, end)
    const avg = slice.reduce((sum, value) => sum + (Number(value) || 0), 0) / (slice.length || 1)
    labels.push(data.labels[end - 1] || data.labels[i] || '')
    values.push(Number(avg.toFixed(2)))
  }

  return { labels, values }
}

export function bucketizeStackedData(data: StackedSeriesData, maxPoints = 120): StackedSeriesData {
  if (!data.labels.length || data.labels.length <= maxPoints) return data

  const bucketSize = Math.ceil(data.labels.length / maxPoints)
  const labels: string[] = []
  const datasets = data.datasets.map((dataset) => ({ name: dataset.name, values: [] as number[] }))

  for (let i = 0; i < data.labels.length; i += bucketSize) {
    const end = Math.min(i + bucketSize, data.labels.length)
    labels.push(data.labels[end - 1] || data.labels[i] || '')

    for (let d = 0; d < data.datasets.length; d++) {
      const source = data.datasets[d]!
      const target = datasets[d]!
      const slice = source.values.slice(i, end)
      const sum = slice.reduce((acc, value) => acc + (Number(value) || 0), 0)
      target.values.push(Number(sum.toFixed(2)))
    }
  }

  return { labels, datasets }
}

export function reducePieData(data: PiePoint[], topN = 12, othersLabel = 'Others'): PiePoint[] {
  if (!data.length || data.length <= topN) return data

  const sorted = [...data].sort((a, b) => (Number(b.value) || 0) - (Number(a.value) || 0))
  const head = sorted.slice(0, topN)
  const tail = sorted.slice(topN)
  const othersValue = tail.reduce((sum, item) => sum + (Number(item.value) || 0), 0)

  if (othersValue <= 0) return head
  return [...head, { name: othersLabel, value: Number(othersValue.toFixed(2)) }]
}

/** Human-readable byte size (1024 base, one decimal below 10). */
export function formatBytes(bytes: number | string | null | undefined): string {
  const value = Number(bytes || 0)
  if (!Number.isFinite(value) || value <= 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  const exp = Math.min(Math.floor(Math.log2(value) / 10), units.length - 1)
  const scaled = value / 1024 ** exp
  const text = scaled >= 100 || exp === 0 ? Math.round(scaled).toString() : scaled.toFixed(1)
  return `${text} ${units[exp]}`
}

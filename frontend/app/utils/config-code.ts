/** Build a stable configuration code from a display name / label. */
export function toConfigCode(value: string, style: 'snake' | 'upper' = 'snake'): string {
  const base = String(value || '')
    .trim()
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .replace(/[^a-zA-Z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
    .slice(0, 48)

  if (!base) return ''
  return style === 'upper' ? base.toUpperCase() : base.toLowerCase()
}

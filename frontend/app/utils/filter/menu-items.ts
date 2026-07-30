export function normalizeToMenuRows(items: unknown[]) {
  if (!items?.length) return []
  const first = items[0]
  if (typeof first === 'string' || typeof first === 'number') {
    return items.map((item) => ({ label: String(item), value: item }))
  }
  return items as { label: string; value: unknown }[]
}

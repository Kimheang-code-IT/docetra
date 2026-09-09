/**
 * Human-readable text for reference/mention field values.
 *
 * Mention and select fields persist objects like { id, label, type } or
 * { id, name }. Rendering them with String() produces "[object Object]".
 * Every list/table/card renderer must go through these helpers.
 */

const LABEL_KEYS = ['label', 'name', 'title', 'fullName', 'fileName'] as const

/** Best display label for a single reference value (scalar or object). */
export function referenceLabel(value: unknown): string {
  if (value == null) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'number' || typeof value === 'boolean') return String(value)
  if (typeof value === 'object') {
    const record = value as Record<string, unknown>
    for (const key of LABEL_KEYS) {
      const candidate = record[key]
      if (typeof candidate === 'string' && candidate.trim()) return candidate
    }
    return ''
  }
  return String(value)
}

/** Comma-joined display text for scalar, object, or array field values. */
export function displayListText(value: unknown): string {
  const text = Array.isArray(value)
    ? value.map(referenceLabel).map(part => part.trim()).filter(Boolean).join(', ')
    : referenceLabel(value)
  return text.trim()
}

/** sessionStorage key for attribute ids to assign after create-from-type flow. */
export const PENDING_TYPE_ATTR_KEY = 'docetra:pending-type-attribute-ids'

export function readPendingTypeAttributeIds(): string[] {
  if (!import.meta.client) return []
  try {
    const raw = sessionStorage.getItem(PENDING_TYPE_ATTR_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw)
    return Array.isArray(parsed) ? parsed.map(String).filter(Boolean) : []
  }
  catch {
    return []
  }
}

export function pushPendingTypeAttributeId(id: string) {
  if (!import.meta.client || !id) return
  const next = [...new Set([...readPendingTypeAttributeIds(), id])]
  sessionStorage.setItem(PENDING_TYPE_ATTR_KEY, JSON.stringify(next))
}

export function clearPendingTypeAttributeIds() {
  if (!import.meta.client) return
  sessionStorage.removeItem(PENDING_TYPE_ATTR_KEY)
}

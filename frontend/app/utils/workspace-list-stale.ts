/** Keys of entity lists/boards that should soft-refresh after a create. */
const staleKeys = new Set<string>()

export function markListStale(...keys: string[]) {
  for (const key of keys) {
    if (key) staleKeys.add(key)
  }
}

/** Returns true if any key was stale (and clears those keys). */
export function consumeListStale(...keys: string[]): boolean {
  let hit = false
  for (const key of keys) {
    if (!key) continue
    if (staleKeys.has(key)) {
      staleKeys.delete(key)
      hit = true
    }
  }
  return hit
}

/** Board/list create flows: skip post-create detail remount. */
export function returnsToListAfterCreate(entityKey: string): boolean {
  return [
    'meetingTopics',
    'meetingHistory',
    'incomingDocuments',
    'outgoingDocuments',
    'documents',
    'masterListRequests',
    'users',
    'roles',
    'officers',
    'departments',
    'companies',
    'purposes',
    'sectors',
  ].includes(entityKey)
}

/** True when create should go back to the list instead of the new record. */
export function shouldReturnToListAfterCreate(entityKey: string, returnTo: unknown): boolean {
  const path = resolveCreateReturnTo(returnTo, '')
  return Boolean(path) || returnsToListAfterCreate(entityKey)
}

/** Safe in-app return path from `?returnTo=`. */
export function resolveCreateReturnTo(
  returnTo: unknown,
  fallback: string,
): string {
  if (typeof returnTo === 'string' && returnTo.startsWith('/') && !returnTo.startsWith('//')) {
    return returnTo
  }
  return fallback
}

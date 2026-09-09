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

/**
 * After create, always return to the collection list/board.
 * Kept for callers/tests; prefer `shouldReturnToListAfterCreate`.
 */
export function returnsToListAfterCreate(_entityKey: string): boolean {
  return true
}

/**
 * Create submit navigates to the main list (or an explicit safe `?returnTo=`).
 * Never stay on `/new` or jump to the new detail page by default.
 */
export function shouldReturnToListAfterCreate(_entityKey: string, _returnTo: unknown): boolean {
  return true
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

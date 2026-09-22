/**
 * Client-session stale-while-revalidate cache for list/board data.
 *
 * Navigating between pages should not hit the API for data that has not
 * changed. Composables read this cache on mount: a fresh entry paints instantly
 * with no loading state, a stale entry paints instantly and revalidates in the
 * background, and a missing/invalidated entry loads normally.
 *
 * Keys must include the current identity so one user's rows are never shown to
 * another in a shared browser session.
 */
export const LIST_CACHE_TTL_MS = 30_000

type CacheEntry = { data: unknown; ts: number }

const store = new Map<string, CacheEntry>()

export function readListCache<T>(key: string): { data: T; fresh: boolean } | null {
  const entry = store.get(key)
  if (!entry) return null
  return { data: entry.data as T, fresh: Date.now() - entry.ts < LIST_CACHE_TTL_MS }
}

export function writeListCache(key: string, data: unknown): void {
  store.set(key, { data, ts: Date.now() })
}

/** Drop every cached list (e.g. on sign-out). */
export function clearListCache(): void {
  store.clear()
}

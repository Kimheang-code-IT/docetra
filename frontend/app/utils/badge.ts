/**
 * Badge color helpers — normalize arbitrary color strings to the Nuxt UI
 * badge union. Pure functions (no Nuxt/Vue imports) so they stay testable.
 */
import type { BadgeColor } from '~/types/docetra/badge'
import { BADGE_COLORS } from '~/types/docetra/badge'

export type { BadgeColor }

export function isBadgeColor(value: unknown): value is BadgeColor {
  return typeof value === 'string' && (BADGE_COLORS as string[]).includes(value)
}

/**
 * Normalize an arbitrary color to the badge union. Hex/custom strings are
 * rejected (callers fall back to heuristics) so UBadge never receives junk.
 */
export function normalizeBadgeColor(value: unknown): BadgeColor | null {
  return isBadgeColor(value) ? value : null
}

/**
 * Pure vocabulary merge/color helpers — DB enum values merged over TS
 * fallback constants. No Nuxt/Vue imports so it stays unit-testable.
 */
import type { BadgeColor, EnumValueOption } from '~/types/docetra/vocabulary'
import { BADGE_COLORS } from '~/types/docetra/vocabulary'

/** Fallback option shape used by config/entities.ts and filter schemas. */
export interface VocabularyFallbackOption {
  label: string
  value: string
  labelKey?: string
  color?: string
}

export interface ResolvedVocabularyOption {
  label: string
  value: string
  labelKey?: string
  color?: BadgeColor | string
}

function isBadgeColor(value: unknown): value is BadgeColor {
  return typeof value === 'string' && (BADGE_COLORS as string[]).includes(value)
}

/**
 * Normalize an arbitrary color to the badge union. Hex/custom strings are
 * rejected (callers fall back to heuristics) so UBadge never receives junk.
 */
export function normalizeBadgeColor(value: unknown): BadgeColor | null {
  return isBadgeColor(value) ? value : null
}

/**
 * Merge server enum values over fallback constants:
 * - union by `code` — custom server-only codes appear after matched entries;
 * - server wins for label source / order / color;
 * - inactive server entries drop the code entirely (admin disabled it).
 * `resolveLabel` localizes server labels (km/en); fallback entries keep their
 * `labelKey` so existing i18n rendering is preserved offline.
 */
export function mergeVocabularyOptions(
  fallback: ReadonlyArray<VocabularyFallbackOption>,
  serverValues: ReadonlyArray<EnumValueOption> | null | undefined,
  resolveLabel: (value: EnumValueOption) => string,
): ResolvedVocabularyOption[] {
  const activeServer = (serverValues || []).filter(value => value.isActive !== false)
  if (!activeServer.length) {
    return fallback.map(entry => ({
      label: entry.label,
      value: entry.value,
      ...(entry.labelKey ? { labelKey: entry.labelKey } : {}),
      ...(entry.color ? { color: entry.color } : {}),
    }))
  }

  const byCode = new Map(activeServer.map(value => [String(value.code).toLowerCase(), value]))
  const seen = new Set<string>()
  const entries: Array<{ option: ResolvedVocabularyOption, order: number }> = []

  const push = (option: ResolvedVocabularyOption, order: number) =>
    entries.push({ option, order })

  fallback.forEach((entry, index) => {
    const server = byCode.get(String(entry.value).toLowerCase())
    if (!server) {
      push({
        label: entry.label,
        value: entry.value,
        ...(entry.labelKey ? { labelKey: entry.labelKey } : {}),
        ...(entry.color ? { color: entry.color } : {}),
      }, index)
      return
    }
    seen.add(String(server.code).toLowerCase())
    push({ label: resolveLabel(server), value: String(server.code), color: normalizeBadgeColor(server.color) || undefined }, orderOf(server) ?? index)
  })

  for (const server of activeServer) {
    const code = String(server.code).toLowerCase()
    if (seen.has(code)) continue
    seen.add(code)
    push({ label: resolveLabel(server), value: String(server.code), color: normalizeBadgeColor(server.color) || undefined }, orderOf(server) ?? Number.MAX_SAFE_INTEGER)
  }

  return entries
    .sort((a, b) => a.order - b.order)
    .map(entry => entry.option)
}

function orderOf(value: EnumValueOption): number | null {
  return typeof value?.order === 'number' && Number.isFinite(value.order) ? value.order : null
}

/** Locale-aware label for a server enum value. */
export function enumValueLabel(
  value: Pick<EnumValueOption, 'code' | 'labelEn' | 'labelKm'>,
  locale: string,
): string {
  const km = locale.toLowerCase().startsWith('km')
  const primary = km ? value.labelKm : value.labelEn
  const secondary = km ? value.labelEn : value.labelKm
  return primary || secondary || value.code
}

/**
 * Vocabulary-driven badge color for a group/code pair, or null when the
 * catalog has no usable color (caller applies its own heuristics).
 */
export function vocabularyBadgeColor(
  catalog: Record<string, EnumValueOption[]> | null | undefined,
  group: string,
  code: unknown,
): BadgeColor | null {
  if (!catalog || !code) return null
  const needle = String(code).toLowerCase()
  const value = (catalog[group] || []).find(item => String(item.code).toLowerCase() === needle)
  return value ? normalizeBadgeColor(value.color) : null
}

/**
 * Map a record-type code to its card-display entity key. Custom types share
 * the generic record bucket (`documents`) — the unified record model renders
 * one card layout family.
 */
export function cardEntityKeyForRecordType(code: string | null | undefined):
  'meetingTopics' | 'meetingHistory' | 'incomingDocuments' | 'outgoingDocuments' | 'documents' | 'masterListRequests' {
  switch (code) {
    case 'meeting_topic': return 'meetingTopics'
    case 'meeting_history': return 'meetingHistory'
    case 'incoming_document': return 'incomingDocuments'
    case 'outgoing_document': return 'outgoingDocuments'
    case 'master_list_request': return 'masterListRequests'
    default: return 'documents'
  }
}

/**
 * DB-driven vocabularies (GET /api/v2/configuration/enums) merged over TS
 * fallback constants. Render rule: consumers render immediately from their
 * fallback arrays; server values merge in within the 60s cache window and
 * never block first paint (no awaited fetch in any setup path).
 */
import type { BadgeColor, EnumValueOption, VocabularyCatalog } from '~/types/docetra/vocabulary'
import { useVocabularyRepository } from '~/repositories'
import {
  enumValueLabel,
  mergeVocabularyOptions,
  vocabularyBadgeColor,
} from '~/utils/vocabulary'
import type { ResolvedVocabularyOption, VocabularyFallbackOption } from '~/utils/vocabulary'

const CACHE_TTL_MS = 60_000

/** Client-side cache only: loadCatalog() no-ops on the server, so a module ref
 *  is safe (no cross-request leakage) and needs no Nuxt instance at import time. */
const catalogState = ref<VocabularyCatalog | null>(null)
const fetchedAtState = ref(0)
/** Module-level so every useVocabulary() instance shares one in-flight GET. */
let inflight: Promise<void> | null = null

function isCacheFresh(): boolean {
  return catalogState.value != null && Date.now() - fetchedAtState.value < CACHE_TTL_MS
}

async function loadCatalog(force: boolean): Promise<void> {
  if (!import.meta.client) return
  if (!force && isCacheFresh()) return
  if (inflight && !force) return inflight

  inflight = (async () => {
    try {
      const response = await useVocabularyRepository().getCatalog()
      catalogState.value = response.data?.groups || {}
      fetchedAtState.value = Date.now()
    }
    catch {
      // Failure path keeps fallbacks authoritative — never surfaces to users.
    }
    finally {
      inflight = null
    }
  })()
  return inflight
}

export function invalidateVocabularyCache(): void {
  catalogState.value = null
  fetchedAtState.value = 0
  void loadCatalog(true)
}

export function useVocabulary() {
  const { locale } = useI18n()

  // Kick off non-blocking; first paint always renders from fallbacks.
  if (import.meta.client && !catalogState.value && !inflight) {
    void loadCatalog(false)
  }

  /** Raw server entries for a group (including inactive), for admin editors. */
  function rawGroup(group: string): EnumValueOption[] {
    return catalogState.value?.[group] || []
  }

  /**
   * Merged options for a group. Fallback array is the instant/offline source;
   * server wins for labels/order/colors and custom codes are appended.
   */
  function options(
    group: string,
    fallback: ReadonlyArray<VocabularyFallbackOption> = [],
  ): ComputedRef<ResolvedVocabularyOption[]> {
    return computed(() => mergeVocabularyOptions(
      fallback,
      catalogState.value?.[group] || null,
      value => enumValueLabel(value, locale.value),
    ))
  }

  /** Vocabulary color for group/code constrained to the badge union, else null. */
  function colorOf(group: string, code: unknown): BadgeColor | null {
    return vocabularyBadgeColor(catalogState.value, group, code)
  }

  return {
    options,
    rawGroup,
    colorOf,
    ready: computed(() => catalogState.value != null),
    refresh: () => loadCatalog(true),
  }
}

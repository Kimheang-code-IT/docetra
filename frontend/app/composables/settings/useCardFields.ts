/**
 * Resolve which board-card slots are visible for an entity.
 *
 * Resolution per slot: record-type payload override (`record_type.payload
 * .cardFields`, provided by document/board loaders via injection) → App Config
 * display settings → catalog defaults from utils/card-fields.ts.
 */
import { inject, provide } from 'vue'
import type { InjectionKey } from 'vue'
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import type { CardFooterAlign } from '~/utils/card-fields'
import type { RecordTypePayload } from '~/types/docetra/vocabulary'
import { useSettingsRepositories } from '~/repositories'
import {
  resolveFooterAlign,
  resolveTypeAwareCardFields,
  resolveTypeAwareFooterAlign,
} from '~/utils/card-fields'

export type CardFieldsOverride = MaybeRefOrGetter<RecordTypePayload | null | undefined>

/** Provide a record-type payload so nested useCardFields() calls become type-aware. */
export const CARD_FIELDS_OVERRIDE_KEY: InjectionKey<CardFieldsOverride> = Symbol('docetra:card-fields-override')

type FieldsCache = Partial<Record<CardDisplayEntityKey, string[]>>
type AlignCache = Partial<Record<CardDisplayEntityKey, Partial<Record<string, CardFooterAlign>>>>

const cardFieldsCache = ref<FieldsCache | null>(null)
const footerAlignCache = ref<AlignCache>({})
let loadPromise: Promise<void> | null = null

async function ensureCardFieldsLoaded(force = false) {
  if (!import.meta.client) return
  if (cardFieldsCache.value && !force) return
  if (loadPromise && !force) return loadPromise

  loadPromise = (async () => {
    try {
      const { appConfig } = useSettingsRepositories()
      const config = await appConfig.get()
      cardFieldsCache.value = { ...(config.display?.cardFields || {}) }
      footerAlignCache.value = { ...(config.display?.cardFooterAlign || {}) }
    }
    catch {
      cardFieldsCache.value = cardFieldsCache.value || {}
    }
    finally {
      loadPromise = null
    }
  })()

  return loadPromise
}

export function invalidateCardFieldsCache() {
  cardFieldsCache.value = null
  loadPromise = null
  void ensureCardFieldsLoaded(true)
}

/** Share one override down the tree (document show/create, stage boards). */
export function provideCardFieldsOverride(override: CardFieldsOverride) {
  provide(CARD_FIELDS_OVERRIDE_KEY, override)
}

function readOverride(): RecordTypePayload | null {
  const injected = inject(CARD_FIELDS_OVERRIDE_KEY, null)
  if (!injected) return null
  const value = toValue(injected)
  return value && typeof value === 'object' ? value : null
}

export function useCardFields(entityKey: MaybeRefOrGetter<CardDisplayEntityKey>) {
  const key = computed(() => toValue(entityKey))
  const typeOverride = readOverride()

  onMounted(() => {
    ensureCardFieldsLoaded()
  })

  const visibleSlots = computed(() => resolveTypeAwareCardFields(key.value, {
    typeOverride: typeOverride?.cardFields || null,
    appConfig: cardFieldsCache.value,
  }))

  function show(slot: string) {
    return visibleSlots.value.includes(slot)
  }

  function footerAlign(slot: string): CardFooterAlign {
    return resolveTypeAwareFooterAlign(key.value, slot, {
      typeOverride: typeOverride?.cardFooterAlign || null,
      appConfig: footerAlignCache.value,
    })
  }

  /** Legacy helper kept for callers that pass an explicit align map. */
  function footerAlignFromMap(
    slot: string,
    map: Partial<Record<CardDisplayEntityKey, Partial<Record<string, CardFooterAlign>>>> | null | undefined,
  ): CardFooterAlign {
    return resolveFooterAlign(key.value, slot, map)
  }

  async function refresh() {
    await ensureCardFieldsLoaded(true)
  }

  return {
    visibleSlots,
    show,
    footerAlign,
    footerAlignFromMap,
    refresh,
    pending: computed(() => cardFieldsCache.value == null),
  }
}

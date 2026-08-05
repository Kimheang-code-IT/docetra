/**
 * Resolve which board-card slots are visible for an entity from App Config.
 */
import type { CardDisplayEntityKey } from '~/types/docetra/settings'
import type { CardFooterAlign } from '~/utils/card-fields'
import { useSettingsRepositories } from '~/repositories'
import { resolveFooterAlign, resolveVisibleSlots } from '~/utils/card-fields'

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

export function useCardFields(entityKey: MaybeRefOrGetter<CardDisplayEntityKey>) {
  const key = computed(() => toValue(entityKey))

  onMounted(() => {
    ensureCardFieldsLoaded()
  })

  const visibleSlots = computed(() => {
    const selected = cardFieldsCache.value?.[key.value]
    return resolveVisibleSlots(key.value, selected)
  })

  function show(slot: string) {
    return visibleSlots.value.includes(slot)
  }

  function footerAlign(slot: string): CardFooterAlign {
    return resolveFooterAlign(key.value, slot, footerAlignCache.value)
  }

  async function refresh() {
    await ensureCardFieldsLoaded(true)
  }

  return {
    visibleSlots,
    show,
    footerAlign,
    refresh,
    pending: computed(() => cardFieldsCache.value == null),
  }
}

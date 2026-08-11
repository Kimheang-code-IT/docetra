/**
 * Merge static entity document tabs with fields from the selected record type.
 */
import type { DocumentTabSchema, FieldOption } from '~/types/docetra/common'
import type { RecordAttribute, RecordType, ResolvedRecordTypeSchema } from '~/types/docetra/configuration'
import { useConfigurationRepositories } from '~/repositories'
import {
  mapTypeAttributesToSections,
  pruneDetailsForType,
  stageOptionsFromType,
} from '~/utils/record-type-fields'

const SCHEMA_CACHE_TTL_MS = 60_000
const schemaCache = new Map<string, {
  at: number
  data?: ResolvedRecordTypeSchema
  inflight?: Promise<ResolvedRecordTypeSchema | null>
}>()

function schemaCacheKey(lookup: { id?: string, code?: string }) {
  if (lookup.id) return `id:${lookup.id}`
  if (lookup.code) return `code:${lookup.code}`
  return ''
}

export function useRecordTypeDrivenTabs(options: {
  entityKey: string
  recordBacked?: boolean
  recordTypeCode?: string
  baseTabs: DocumentTabSchema[]
  getRecordTypeId: () => string | undefined
  getDetails: () => Record<string, unknown> | undefined
  setDetails: (details: Record<string, unknown>) => void
  setStageIfEmpty?: (stage: string) => void
}) {
  const { recordTypes } = useConfigurationRepositories()
  const { t } = useI18n()

  const loadedType = ref<RecordType | null>(null)
  const catalog = ref<RecordAttribute[]>([])
  const loadingType = ref(false)
  let loadSeq = 0

  const enabled = computed(() => options.recordBacked === true)

  async function resolveSchema(typeId: string | undefined) {
    const id = String(typeId || '').trim()
    const code = String(options.recordTypeCode || '').trim()
    const lookup = id ? { id } : code ? { code } : null
    if (!lookup) return null

    const key = schemaCacheKey(lookup)
    const cached = schemaCache.get(key)
    if (cached?.inflight) return cached.inflight
    if (cached?.data && Date.now() - cached.at < SCHEMA_CACHE_TTL_MS) {
      return cached.data
    }

    const inflight = recordTypes.getResolvedSchema(lookup)
      .then((schema) => {
        schemaCache.set(key, { at: Date.now(), data: schema })
        return schema
      })
      .catch((error) => {
        schemaCache.delete(key)
        throw error
      })
    schemaCache.set(key, { at: 0, inflight })
    return inflight
  }

  async function loadType(typeId: string | undefined, opts?: { prune?: boolean }) {
    if (!enabled.value) {
      loadedType.value = null
      return
    }
    const lookupKey = String(typeId || options.recordTypeCode || '').trim()
    if (!lookupKey) {
      loadedType.value = null
      if (opts?.prune) options.setDetails({})
      return
    }
    const seq = ++loadSeq
    loadingType.value = true
    try {
      const schema = await resolveSchema(typeId)
      if (seq !== loadSeq) return
      if (!schema) {
        loadedType.value = null
        return
      }
      const type = schema.recordType
      catalog.value = schema.attributes
      loadedType.value = type
      if (opts?.prune) {
        const pruned = pruneDetailsForType(options.getDetails(), type.attributes || [])
        options.setDetails(pruned)
      }
      const initial = type.stages?.find(s => s.isInitial)?.code || type.stages?.[0]?.code
      if (initial) options.setStageIfEmpty?.(initial)
    }
    catch {
      if (seq !== loadSeq) return
      loadedType.value = null
    }
    finally {
      if (seq === loadSeq) loadingType.value = false
    }
  }

  const tabs = computed<DocumentTabSchema[]>(() => {
    const base = options.baseTabs
    if (!enabled.value) return base

    const type = loadedType.value
    const stageOptions = stageOptionsFromType(type)
    const typeSections = type
      ? mapTypeAttributesToSections(
          type.attributes || [],
          catalog.value,
          t('docetra.config.typeFields'),
        )
      : []

    return base.map((tab) => {
      if (tab.id !== 'details') return tab

      const sections = tab.sections.map((section) => {
        const fields = section.fields.map((field) => {
          if (field.key !== 'stage' || !stageOptions?.length) return field
          return {
            ...field,
            options: stageOptions as FieldOption[],
          }
        })
        return { ...section, fields }
      })

      return {
        ...tab,
        sections: [...sections, ...typeSections],
      }
    })
  })

  watch(
    () => [options.getRecordTypeId(), options.recordTypeCode] as const,
    (current, previous) => {
      const [id] = current
      const prevId = previous?.[0]
      if (!enabled.value) return
      const changed = prevId !== undefined && prevId !== id
      void loadType(id, { prune: changed })
    },
    { immediate: true },
  )

  return {
    tabs,
    loadedType,
    loadingType,
    enabled,
    reload: () => loadType(options.getRecordTypeId()),
  }
}

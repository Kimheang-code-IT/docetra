/**
 * Merge static entity document tabs with fields from the selected record type.
 */
import type { DocumentTabSchema, FieldOption } from '~/types/docetra/common'
import type { RecordAttribute, RecordType } from '~/types/docetra/configuration'
import { useConfigurationRepositories } from '~/repositories'
import {
  mapTypeAttributesToSections,
  pruneDetailsForType,
  stageOptionsFromType,
} from '~/utils/record-type-fields'

export const RECORD_TYPE_DRIVEN_KEYS = new Set([
  'incomingDocuments',
  'outgoingDocuments',
  'documents',
  'masterListRequests',
])

export function useRecordTypeDrivenTabs(options: {
  entityKey: string
  baseTabs: DocumentTabSchema[]
  getRecordTypeId: () => string | undefined
  getDetails: () => Record<string, unknown> | undefined
  setDetails: (details: Record<string, unknown>) => void
  setStageIfEmpty?: (stage: string) => void
}) {
  const { recordTypes, attributes } = useConfigurationRepositories()
  const { t } = useI18n()

  const loadedType = ref<RecordType | null>(null)
  const catalog = ref<RecordAttribute[]>([])
  const loadingType = ref(false)
  let loadSeq = 0

  const enabled = computed(() => RECORD_TYPE_DRIVEN_KEYS.has(options.entityKey))

  async function ensureCatalog() {
    if (catalog.value.length) return
    const res = await attributes.list({ limit: 200, status: 'active' })
    catalog.value = res.data || []
  }

  async function loadType(typeId: string | undefined, opts?: { prune?: boolean }) {
    if (!enabled.value) {
      loadedType.value = null
      return
    }
    const id = String(typeId || '').trim()
    if (!id) {
      loadedType.value = null
      if (opts?.prune) options.setDetails({})
      return
    }
    const seq = ++loadSeq
    loadingType.value = true
    try {
      await ensureCatalog()
      const type = await recordTypes.getById(id)
      if (seq !== loadSeq) return
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
    () => options.getRecordTypeId(),
    (id, prev) => {
      if (!enabled.value) return
      const changed = prev !== undefined && prev !== id
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

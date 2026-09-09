import { buildEntityConfigForType } from '~/config/entities'
import { useRecordSurfaces } from '~/composables/record/useRecordSurfaces'

/** Resolve the active `/meetings|records/{typeCode}` surface from the live route. */
export async function useRecordSurfacePage(uiSurface: 'meeting' | 'document') {
  const route = useRoute()
  const { load, resolveByParam } = useRecordSurfaces()
  await load()

  const param = computed(() => String(route.params.typeCode || ''))
  const surface = computed(() => resolveByParam(uiSurface, param.value))
  const missingMessage = uiSurface === 'meeting' ? 'Meeting type not found' : 'Record type not found'

  if (!surface.value) {
    throw createError({ statusCode: 404, statusMessage: missingMessage })
  }

  watch(param, () => {
    if (!surface.value) {
      showError(createError({ statusCode: 404, statusMessage: missingMessage }))
    }
  })

  const config = computed(() => {
    const current = surface.value
    if (!current) {
      return buildEntityConfigForType({
        typeCode: param.value || 'unknown',
        name: missingMessage,
        routeBase: route.path,
        uiSurface,
      })
    }
    return buildEntityConfigForType({
      typeCode: current.code,
      name: current.name,
      routeBase: current.routeBase,
      uiSurface,
      icon: current.icon,
      isCreatable: current.isCreatable,
      supportsStages: current.supportsStages,
      supportsTopicContainer: uiSurface === 'meeting' ? current.supportsTopicContainer : undefined,
    })
  })

  const pageKey = computed(() => route.path)

  return { param, surface, config, pageKey }
}

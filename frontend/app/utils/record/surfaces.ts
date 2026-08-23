import type { RecordSurfaceType } from '~/composables/record/useRecordSurfaces'

export function resolveRecordSurfaceByParam(
  types: RecordSurfaceType[],
  param: string,
): RecordSurfaceType | null {
  const needle = String(param || '').trim().toLowerCase()
  if (!needle) return null
  return types.find(type =>
    type.code.toLowerCase() === needle
    || String(type.slug || '').toLowerCase() === needle
    || type.routeBase.toLowerCase().endsWith(`/${needle}`),
  ) || null
}

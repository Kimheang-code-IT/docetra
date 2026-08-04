import type { RecordAttributeRepository, RecordTypeRepository } from '~/repositories/contracts/configuration'
import type { ApiResponse } from '~/types/docetra/common'
import type { RecordAttribute, RecordType } from '~/types/docetra/configuration'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'
import { unwrapApiData } from './response'

export function createHttpRecordAttributeRepository(): RecordAttributeRepository {
  const api = useApi()
  const resource = (id: string) => `${ApiEndpoints.RECORD_ATTRIBUTES}/${encodeURIComponent(id)}`

  return {
    list: query => api.get<ApiResponse<RecordAttribute[]>>(ApiEndpoints.RECORD_ATTRIBUTES, { query }),
    getById: async id => unwrapApiData(await api.get<RecordAttribute | ApiResponse<RecordAttribute>>(resource(id))),
    create: async input => unwrapApiData(await api.post<RecordAttribute | ApiResponse<RecordAttribute>>(ApiEndpoints.RECORD_ATTRIBUTES, input)),
    update: async (id, input) => unwrapApiData(await api.patch<RecordAttribute | ApiResponse<RecordAttribute>>(resource(id), input)),
    duplicate: async id => unwrapApiData(await api.post<RecordAttribute | ApiResponse<RecordAttribute>>(`${resource(id)}/duplicate`, {})),
    setActive: async (id, active) => unwrapApiData(await api.patch<RecordAttribute | ApiResponse<RecordAttribute>>(`${resource(id)}/status`, { active })),
    remove: async id => { await api.delete(resource(id)) },
  }
}

export function createHttpRecordTypeRepository(): RecordTypeRepository {
  const api = useApi()
  const resource = (id: string) => `${ApiEndpoints.RECORD_TYPES}/${encodeURIComponent(id)}`

  return {
    list: query => api.get<ApiResponse<RecordType[]>>(ApiEndpoints.RECORD_TYPES, { query }),
    getById: async id => unwrapApiData(await api.get<RecordType | ApiResponse<RecordType>>(resource(id))),
    create: async input => unwrapApiData(await api.post<RecordType | ApiResponse<RecordType>>(ApiEndpoints.RECORD_TYPES, input)),
    update: async (id, input) => unwrapApiData(await api.patch<RecordType | ApiResponse<RecordType>>(resource(id), input)),
    duplicate: async id => unwrapApiData(await api.post<RecordType | ApiResponse<RecordType>>(`${resource(id)}/duplicate`, {})),
    setActive: async (id, active) => unwrapApiData(await api.patch<RecordType | ApiResponse<RecordType>>(`${resource(id)}/status`, { active })),
    remove: async id => { await api.delete(resource(id)) },
  }
}

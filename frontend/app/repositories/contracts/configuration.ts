import type { ApiResponse } from '~/types/docetra/common'
import type {
  CreateRecordAttributeInput,
  CreateRecordTypeInput,
  RecordAttribute,
  RecordAttributeQuery,
  RecordType,
  RecordTypeQuery,
  UpdateRecordAttributeInput,
  UpdateRecordTypeInput,
} from '~/types/docetra/configuration'

export interface RecordAttributeRepository {
  list: (query?: RecordAttributeQuery) => Promise<ApiResponse<RecordAttribute[]>>
  getById: (id: string) => Promise<RecordAttribute>
  create: (input: CreateRecordAttributeInput) => Promise<RecordAttribute>
  update: (id: string, input: UpdateRecordAttributeInput) => Promise<RecordAttribute>
  duplicate: (id: string) => Promise<RecordAttribute>
  setActive: (id: string, active: boolean) => Promise<RecordAttribute>
  remove: (id: string) => Promise<void>
}

export interface RecordTypeRepository {
  list: (query?: RecordTypeQuery) => Promise<ApiResponse<RecordType[]>>
  getById: (id: string) => Promise<RecordType>
  create: (input: CreateRecordTypeInput) => Promise<RecordType>
  update: (id: string, input: UpdateRecordTypeInput) => Promise<RecordType>
  duplicate: (id: string) => Promise<RecordType>
  setActive: (id: string, active: boolean) => Promise<RecordType>
  remove: (id: string) => Promise<void>
}

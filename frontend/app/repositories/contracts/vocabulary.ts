import type {
  CreateEnumValueInput,
  EnumValueOption,
  UpdateEnumValueInput,
  VocabularyCatalog,
} from '~/types/docetra/vocabulary'
import type { ApiResponse } from '~/types/docetra/common'

export interface VocabularyRepositoryContract {
  /** Full grouped catalog (public groups honor public_access server-side). */
  getCatalog: () => Promise<ApiResponse<{ groups: VocabularyCatalog }>>
  createValue: (group: string, input: CreateEnumValueInput) => Promise<EnumValueOption>
  updateValue: (group: string, code: string, input: UpdateEnumValueInput) => Promise<EnumValueOption>
  deleteValue: (group: string, code: string) => Promise<void>
}

export interface PermissionCatalogRepositoryContract {
  list: () => Promise<ApiResponse<string[]>>
}

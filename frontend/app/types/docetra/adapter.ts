import type {
  ActivityEvent,
  ApiResponse,
  AttachmentMeta,
  EntityComment,
  ListQuery,
} from '~/types/docetra/common'

export interface EntityAdapter<T> {
  list: (query?: ListQuery) => Promise<ApiResponse<T[]>>
  get: (id: string) => Promise<ApiResponse<T>>
  create: (payload: Partial<T>) => Promise<ApiResponse<T>>
  update: (id: string, payload: Partial<T>) => Promise<ApiResponse<T>>
  delete?: (id: string) => Promise<ApiResponse<{ id: string }>>
  deleteMany?: (ids: string[]) => Promise<ApiResponse<{ ids: string[] }>>
  transitionStage?: (id: string, stage: string) => Promise<ApiResponse<T>>
  listByStage?: (stage: string, query?: ListQuery) => Promise<ApiResponse<T[]>>
  listComments?: (id: string, query?: ListQuery) => Promise<ApiResponse<EntityComment[]>>
  addComment?: (id: string, body: string) => Promise<ApiResponse<EntityComment>>
  listActivity?: (id: string, query?: ListQuery) => Promise<ApiResponse<ActivityEvent[]>>
  listAttachments?: (id: string) => Promise<ApiResponse<AttachmentMeta[]>>
}

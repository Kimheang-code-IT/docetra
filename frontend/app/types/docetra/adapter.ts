import type {
  ActivityEvent,
  ApiResponse,
  AttachmentMeta,
  EntityComment,
  EntityFavoriteState,
  EntityRecordNeighbors,
  GroupCountSummary,
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
  /** One aggregate request; avoids one count request per board column. */
  getGroupCounts?: (field: string, query?: ListQuery) => Promise<ApiResponse<GroupCountSummary>>
  listComments?: (id: string, query?: ListQuery) => Promise<ApiResponse<EntityComment[]>>
  addComment?: (id: string, body: string, author?: EntityComment['author']) => Promise<ApiResponse<EntityComment>>
  updateComment?: (id: string, commentId: string, body: string) => Promise<ApiResponse<EntityComment>>
  deleteComment?: (id: string, commentId: string) => Promise<ApiResponse<{ id: string }>>
  getNeighbors?: (id: string, query?: Pick<ListQuery, 'sort'>) => Promise<ApiResponse<EntityRecordNeighbors>>
  getFavorite?: (id: string, userId?: string) => Promise<ApiResponse<EntityFavoriteState>>
  setFavorite?: (id: string, isFavorite: boolean, userId?: string) => Promise<ApiResponse<EntityFavoriteState>>
  listActivity?: (id: string, query?: ListQuery) => Promise<ApiResponse<ActivityEvent[]>>
  listAttachments?: (id: string, query?: ListQuery) => Promise<ApiResponse<AttachmentMeta[]>>
  replaceAttachments?: (id: string, files: AttachmentMeta[]) => Promise<ApiResponse<AttachmentMeta[]>>
}

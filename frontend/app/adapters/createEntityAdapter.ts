import type { EntityAdapter } from '~/types/docetra/adapter'
import type {
  ActivityEvent,
  ApiResponse,
  AttachmentMeta,
  EntityComment,
  EntityFavoriteState,
  EntityRecordNeighbors,
  GroupCountSummary,
} from '~/types/docetra/common'

type EntityRecord = { id: string; status?: string; stage?: string; updatedAt?: string; createdAt?: string }

export function createEntityAdapter<T extends EntityRecord>(options: {
  endpoint: string
}): EntityAdapter<T> {
  const { endpoint } = options
  const resource = (id: string) => `${endpoint}/${encodeURIComponent(id)}`
  const api = () => useApi()

  return {
    async list(query) {
      const listScope = [query?.view || 'list', query?.stage || 'all', query?.status || 'all-status'].join(':')
      return api().get<ApiResponse<T[]>>(endpoint, {
        query,
        requestKey: `list:${endpoint}:${listScope}`,
        cancelPrevious: true,
      })
    },

    get(id) {
      return api().get<ApiResponse<T>>(resource(id))
    },

    create(payload) {
      return api().post<ApiResponse<T>>(endpoint, payload)
    },

    update(id, payload) {
      return api().patch<ApiResponse<T>>(resource(id), payload)
    },

    archive(id) {
      return api().post<ApiResponse<T>>(`${resource(id)}/archive`, {})
    },

    restore(id) {
      return api().post<ApiResponse<T>>(`${resource(id)}/restore`, {})
    },

    delete(id) {
      return api().delete<ApiResponse<{ id: string }>>(resource(id))
    },

    deleteMany(ids) {
      return api().post<ApiResponse<{ ids: string[] }>>(`${endpoint}/bulk-delete`, { ids })
    },

    purge(id) {
      return api().delete<ApiResponse<{ id: string }>>(`${resource(id)}/purge`)
    },

    transitionStage(id, stage) {
      return api().patch<ApiResponse<T>>(`${resource(id)}/stage`, { stage })
    },

    listByStage(stage, query) {
      return this.list({ ...query, stage })
    },

    getGroupCounts(field, query) {
      return api().get<ApiResponse<GroupCountSummary>>(`${endpoint}/counts`, {
        query: { ...query, groupBy: field },
        requestKey: `counts:${endpoint}:${field}`,
        cancelPrevious: true,
      })
    },

    listComments(id, query) {
      return api().get<ApiResponse<EntityComment[]>>(`${resource(id)}/comments`, { query })
    },

    addComment(id, body) {
      return api().post<ApiResponse<EntityComment>>(`${resource(id)}/comments`, { body })
    },

    updateComment(id, commentId, body) {
      return api().patch<ApiResponse<EntityComment>>(
        `${resource(id)}/comments/${encodeURIComponent(commentId)}`,
        { body },
      )
    },

    deleteComment(id, commentId) {
      return api().delete<ApiResponse<{ id: string }>>(
        `${resource(id)}/comments/${encodeURIComponent(commentId)}`,
      )
    },

    getNeighbors(id, query) {
      return api().get<ApiResponse<EntityRecordNeighbors>>(`${resource(id)}/neighbors`, {
        query,
        requestKey: `neighbors:${endpoint}:${id}`,
        cancelPrevious: true,
      })
    },

    getFavorite(id) {
      return api().get<ApiResponse<EntityFavoriteState>>(`${resource(id)}/favorite`, {
        requestKey: `favorite:${endpoint}:${id}`,
        cancelPrevious: true,
      })
    },

    setFavorite(id, isFavorite) {
      return api().put<ApiResponse<EntityFavoriteState>>(`${resource(id)}/favorite`, { isFavorite })
    },

    listActivity(id, query) {
      return api().get<ApiResponse<ActivityEvent[]>>(`${resource(id)}/activity`, { query })
    },

    listAttachments(id, query) {
      return api().get<ApiResponse<AttachmentMeta[]>>(`${resource(id)}/attachments`, { query })
    },

    replaceAttachments(id, files) {
      return api().put<ApiResponse<AttachmentMeta[]>>(`${resource(id)}/attachments`, { files })
    },
  }
}

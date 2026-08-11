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
import { applyListQuery, createId, mockLatency, nowIso, ok } from '~/mocks/query'
import { person, seedActivity, seedAttachments, seedComments } from '~/mocks/seed'

type EntityRecord = { id: string; stage?: string; updatedAt?: string; createdAt?: string }

type MockStore<T extends EntityRecord> = {
  items: T[]
  comments: Record<string, EntityComment[]>
  activity: Record<string, ActivityEvent[]>
  attachments: Record<string, AttachmentMeta[]>
  favorites: Record<string, Set<string>>
}

export function createMockStore<T extends EntityRecord>(seed: T[]): MockStore<T> {
  return { items: structuredClone(seed), comments: {}, activity: {}, attachments: {}, favorites: {} }
}

function usesMockData() {
  return useRuntimeConfig().public.useMockData !== false
}

/**
 * One entity contract with two isolated providers: bounded local mock data for
 * development and the versioned REST API for real deployments.
 */
export function createEntityAdapter<T extends EntityRecord>(options: {
  endpoint: string
  store: MockStore<T>
  searchKeys?: string[]
}): EntityAdapter<T> {
  const { endpoint, store, searchKeys } = options
  const resource = (id: string) => `${endpoint}/${encodeURIComponent(id)}`

  return {
    async list(query) {
      if (!usesMockData()) {
        // Keep independent board columns concurrent while replacing stale
        // searches/page requests for the same list consumer.
        const listScope = [query?.view || 'list', query?.stage || 'all'].join(':')
        return useApi().get<ApiResponse<T[]>>(endpoint, {
          query,
          requestKey: `list:${endpoint}:${listScope}`,
          cancelPrevious: true,
        })
      }
      await mockLatency(null)
      return applyListQuery(store.items as unknown as Record<string, unknown>[], query, searchKeys) as unknown as ApiResponse<T[]>
    },

    async get(id) {
      if (!usesMockData()) return useApi().get<ApiResponse<T>>(resource(id))
      await mockLatency(null)
      const item = store.items.find(row => row.id === id)
      if (!item) throw createError({ statusCode: 404, statusMessage: 'Not found' })
      return ok(structuredClone(item))
    },

    async create(payload) {
      if (!usesMockData()) return useApi().post<ApiResponse<T>>(endpoint, payload)
      await mockLatency(null)
      const now = nowIso()
      const item = {
        ...payload,
        id: createId('ent'),
        createdAt: now,
        updatedAt: now,
      } as T
      store.items.unshift(item)
      store.comments[item.id] = []
      store.attachments[item.id] = []
      store.activity[item.id] = seedActivity(endpoint, item.id, 1)
      return ok(structuredClone(item))
    },

    async update(id, payload) {
      if (!usesMockData()) return useApi().patch<ApiResponse<T>>(resource(id), payload)
      await mockLatency(null)
      const index = store.items.findIndex(row => row.id === id)
      if (index < 0) throw createError({ statusCode: 404, statusMessage: 'Not found' })
      const item = { ...store.items[index]!, ...payload, updatedAt: nowIso() } as T
      store.items[index] = item
      store.activity[id] = [
        { id: createId('act'), entityType: endpoint, entityId: id, action: 'updated', actor: person(0), summary: `${person(0).name} updated this record`, occurredAt: nowIso() },
        ...(store.activity[id] || []),
      ]
      return ok(structuredClone(item))
    },

    async delete(id) {
      if (!usesMockData()) return useApi().delete<ApiResponse<{ id: string }>>(resource(id))
      await mockLatency(null)
      const index = store.items.findIndex(row => row.id === id)
      if (index < 0) throw createError({ statusCode: 404, statusMessage: 'Not found' })
      store.items.splice(index, 1)
      delete store.comments[id]
      delete store.activity[id]
      delete store.attachments[id]
      for (const favorites of Object.values(store.favorites)) favorites.delete(id)
      return ok({ id })
    },

    async deleteMany(ids) {
      if (!usesMockData()) return useApi().post<ApiResponse<{ ids: string[] }>>(`${endpoint}/bulk-delete`, { ids })
      await mockLatency(null)
      const idSet = new Set(ids)
      store.items = store.items.filter(row => !idSet.has(row.id))
      for (const id of ids) {
        delete store.comments[id]
        delete store.activity[id]
        delete store.attachments[id]
        for (const favorites of Object.values(store.favorites)) favorites.delete(id)
      }
      return ok({ ids })
    },

    async transitionStage(id, stage) {
      if (!usesMockData()) return useApi().patch<ApiResponse<T>>(`${resource(id)}/stage`, { stage })
      return this.update(id, { stage } as Partial<T>)
    },

    listByStage(stage, query) {
      return this.list({ ...query, stage })
    },

    async getGroupCounts(field, query) {
      if (!usesMockData()) {
        return useApi().get<ApiResponse<GroupCountSummary>>(`${endpoint}/counts`, {
          query: { ...query, groupBy: field },
          requestKey: `counts:${endpoint}:${field}`,
          cancelPrevious: true,
        })
      }
      await mockLatency(null)
      const baseQuery = { ...query, page: 1, limit: 1 }
      const total = applyListQuery(store.items as unknown as Record<string, unknown>[], baseQuery, searchKeys).meta?.total || 0
      const groups: Record<string, number> = {}
      const values = new Set(
        store.items
          .map(item => String((item as Record<string, unknown>)[field] || ''))
          .filter(Boolean),
      )
      for (const value of values) {
        groups[value] = applyListQuery(
          store.items as unknown as Record<string, unknown>[],
          { ...baseQuery, [field]: value },
          searchKeys,
        ).meta?.total || 0
      }
      const unassigned = applyListQuery(
        store.items as unknown as Record<string, unknown>[],
        { ...baseQuery, [field]: '__empty__' },
        searchKeys,
      ).meta?.total || 0
      return ok({ total, unassigned, groups })
    },

    async listComments(id, query) {
      if (!usesMockData()) return useApi().get<ApiResponse<EntityComment[]>>(`${resource(id)}/comments`, { query })
      await mockLatency(null)
      store.comments[id] ||= seedComments(endpoint, id)
      return applyListQuery(store.comments[id] as unknown as Record<string, unknown>[], query, ['body']) as unknown as ApiResponse<EntityComment[]>
    },

    async addComment(id, body, author) {
      if (!usesMockData()) return useApi().post<ApiResponse<EntityComment>>(`${resource(id)}/comments`, { body })
      await mockLatency(null)
      const comment: EntityComment = { id: createId('cmt'), entityType: endpoint, entityId: id, body, author: author || person(0), createdAt: nowIso() }
      store.comments[id] = [comment, ...(store.comments[id] || [])]
      return ok(comment)
    },

    async updateComment(id, commentId, body) {
      if (!usesMockData()) {
        return useApi().patch<ApiResponse<EntityComment>>(
          `${resource(id)}/comments/${encodeURIComponent(commentId)}`,
          { body },
        )
      }
      await mockLatency(null)
      store.comments[id] ||= seedComments(endpoint, id)
      const index = store.comments[id].findIndex(comment => comment.id === commentId)
      if (index < 0) throw createError({ statusCode: 404, statusMessage: 'Comment not found' })
      const comment = { ...store.comments[id][index]!, body, editedAt: nowIso() }
      store.comments[id][index] = comment
      return ok(structuredClone(comment))
    },

    async deleteComment(id, commentId) {
      if (!usesMockData()) {
        return useApi().delete<ApiResponse<{ id: string }>>(
          `${resource(id)}/comments/${encodeURIComponent(commentId)}`,
        )
      }
      await mockLatency(null)
      store.comments[id] ||= seedComments(endpoint, id)
      const index = store.comments[id].findIndex(comment => comment.id === commentId)
      if (index < 0) throw createError({ statusCode: 404, statusMessage: 'Comment not found' })
      store.comments[id].splice(index, 1)
      return ok({ id: commentId })
    },

    async getNeighbors(id, query) {
      if (!usesMockData()) {
        return useApi().get<ApiResponse<EntityRecordNeighbors>>(`${resource(id)}/neighbors`, {
          query,
          requestKey: `neighbors:${endpoint}:${id}`,
          cancelPrevious: true,
        })
      }
      await mockLatency(null)
      const descending = query?.sort?.startsWith('-') !== false
      const sortKey = query?.sort?.replace(/^-/, '') || 'updatedAt'
      const ordered = [...store.items].sort((a, b) => {
        const comparison = String(a[sortKey as keyof T] || '').localeCompare(String(b[sortKey as keyof T] || ''))
        if (comparison) return descending ? -comparison : comparison
        return descending ? b.id.localeCompare(a.id) : a.id.localeCompare(b.id)
      })
      const index = ordered.findIndex(item => item.id === id)
      return ok({
        previousId: index > 0 ? ordered[index - 1]!.id : null,
        nextId: index >= 0 && index < ordered.length - 1 ? ordered[index + 1]!.id : null,
      })
    },

    async getFavorite(id, userId) {
      if (!usesMockData()) {
        return useApi().get<ApiResponse<EntityFavoriteState>>(`${resource(id)}/favorite`, {
          requestKey: `favorite:${endpoint}:${id}`,
          cancelPrevious: true,
        })
      }
      await mockLatency(null)
      const favorites = store.favorites[userId || 'current'] || new Set<string>()
      return ok({ isFavorite: favorites.has(id) })
    },

    async setFavorite(id, isFavorite, userId) {
      if (!usesMockData()) {
        return useApi().put<ApiResponse<EntityFavoriteState>>(`${resource(id)}/favorite`, { isFavorite })
      }
      await mockLatency(null)
      const key = userId || 'current'
      store.favorites[key] ||= new Set<string>()
      if (isFavorite) store.favorites[key].add(id)
      else store.favorites[key].delete(id)
      return ok({ isFavorite })
    },

    async listActivity(id, query) {
      if (!usesMockData()) return useApi().get<ApiResponse<ActivityEvent[]>>(`${resource(id)}/activity`, { query })
      await mockLatency(null)
      store.activity[id] ||= seedActivity(endpoint, id)
      return applyListQuery(store.activity[id] as unknown as Record<string, unknown>[], query, ['summary', 'action']) as unknown as ApiResponse<ActivityEvent[]>
    },

    async listAttachments(id, query) {
      if (!usesMockData()) return useApi().get<ApiResponse<AttachmentMeta[]>>(`${resource(id)}/attachments`, { query })
      await mockLatency(null)
      store.attachments[id] ||= seedAttachments()
      return applyListQuery(
        store.attachments[id] as unknown as Record<string, unknown>[],
        query,
        ['name', 'mimeType'],
      ) as unknown as ApiResponse<AttachmentMeta[]>
    },

    async replaceAttachments(id, files) {
      if (!usesMockData()) return useApi().put<ApiResponse<AttachmentMeta[]>>(`${resource(id)}/attachments`, { files })
      await mockLatency(null)
      store.attachments[id] = structuredClone(files)
      return ok(structuredClone(files))
    },
  }
}

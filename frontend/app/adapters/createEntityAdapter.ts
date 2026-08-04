import type { EntityAdapter } from '~/types/docetra/adapter'
import type { ActivityEvent, ApiResponse, AttachmentMeta, EntityComment } from '~/types/docetra/common'
import { applyListQuery, createId, mockLatency, nowIso, ok } from '~/mocks/query'
import { person, seedActivity, seedAttachments, seedComments } from '~/mocks/seed'

type EntityRecord = { id: string; stage?: string; updatedAt?: string; createdAt?: string }

type MockStore<T extends EntityRecord> = {
  items: T[]
  comments: Record<string, EntityComment[]>
  activity: Record<string, ActivityEvent[]>
  attachments: Record<string, AttachmentMeta[]>
}

export function createMockStore<T extends EntityRecord>(seed: T[]): MockStore<T> {
  return { items: structuredClone(seed), comments: {}, activity: {}, attachments: {} }
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
        return useApi().get<ApiResponse<T[]>>(endpoint, {
          query,
          requestKey: `list:${endpoint}`,
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

    async listComments(id, query) {
      if (!usesMockData()) return useApi().get<ApiResponse<EntityComment[]>>(`${resource(id)}/comments`, { query })
      await mockLatency(null)
      store.comments[id] ||= seedComments(endpoint, id)
      return applyListQuery(store.comments[id] as unknown as Record<string, unknown>[], query, ['body']) as unknown as ApiResponse<EntityComment[]>
    },

    async addComment(id, body) {
      if (!usesMockData()) return useApi().post<ApiResponse<EntityComment>>(`${resource(id)}/comments`, { body })
      await mockLatency(null)
      const comment: EntityComment = { id: createId('cmt'), entityType: endpoint, entityId: id, body, author: person(0), createdAt: nowIso() }
      store.comments[id] = [comment, ...(store.comments[id] || [])]
      return ok(comment)
    },

    async listActivity(id, query) {
      if (!usesMockData()) return useApi().get<ApiResponse<ActivityEvent[]>>(`${resource(id)}/activity`, { query })
      await mockLatency(null)
      store.activity[id] ||= seedActivity(endpoint, id)
      return applyListQuery(store.activity[id] as unknown as Record<string, unknown>[], query, ['summary', 'action']) as unknown as ApiResponse<ActivityEvent[]>
    },

    async listAttachments(id) {
      if (!usesMockData()) return useApi().get<ApiResponse<AttachmentMeta[]>>(`${resource(id)}/attachments`)
      await mockLatency(null)
      store.attachments[id] ||= seedAttachments()
      return ok(structuredClone(store.attachments[id]))
    },

    async replaceAttachments(id, files) {
      if (!usesMockData()) return useApi().put<ApiResponse<AttachmentMeta[]>>(`${resource(id)}/attachments`, { files })
      await mockLatency(null)
      store.attachments[id] = structuredClone(files)
      return ok(structuredClone(files))
    },
  }
}

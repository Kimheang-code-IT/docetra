import type { EntityAdapter } from '~/types/docetra/adapter'
import type { ActivityEvent, AttachmentMeta, EntityComment } from '~/types/docetra/common'
import { applyListQuery, createId, mockLatency, nowIso, ok } from '~/mocks/query'
import { person, seedActivity, seedAttachments, seedComments } from '~/mocks/seed'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

type Store<T extends { id: string }> = {
  items: T[]
  comments: Record<string, EntityComment[]>
  activity: Record<string, ActivityEvent[]>
  attachments: Record<string, AttachmentMeta[]>
}

function getUseMockData() {
  const config = useRuntimeConfig()
  return config.public.useMockData !== false
}

export function createEntityAdapter<T extends { id: string; stage?: string; updatedAt?: string }>(options: {
  endpoint: string
  store: Store<T>
  searchKeys?: string[]
  createDefaults?: (payload: Partial<T>) => T
}): EntityAdapter<T> {
  const { endpoint, store, searchKeys, createDefaults } = options

  return {
    async list(query) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.get(endpoint, { query }) as any
      }
      await mockLatency(null)
      return applyListQuery(store.items as any, query, searchKeys)
    },

    async get(id) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.get(`${endpoint}/${id}`) as any
      }
      await mockLatency(null)
      const item = store.items.find(x => x.id === id)
      if (!item) throw createError({ statusCode: 404, statusMessage: 'Not found' })
      return ok(item)
    },

    async create(payload) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.post(endpoint, payload as any) as any
      }
      await mockLatency(null)
      const item = createDefaults
        ? createDefaults(payload)
        : ({
            ...payload,
            id: createId('ent'),
            createdAt: nowIso(),
            updatedAt: nowIso(),
          } as unknown as T)
      store.items.unshift(item)
      store.comments[item.id] = []
      store.activity[item.id] = [{
        id: createId('act'),
        entityType: endpoint,
        entityId: item.id,
        action: 'created',
        actor: person(0),
        summary: `${person(0).name} created this record`,
        occurredAt: nowIso(),
      }]
      store.attachments[item.id] = []
      return ok(item)
    },

    async update(id, payload) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.patch(`${endpoint}/${id}`, payload as any) as any
      }
      await mockLatency(null)
      const index = store.items.findIndex(x => x.id === id)
      if (index < 0) throw createError({ statusCode: 404, statusMessage: 'Not found' })
      const updated = {
        ...store.items[index]!,
        ...payload,
        updatedAt: nowIso(),
      } as T
      store.items[index] = updated
      const activity = store.activity[id] || []
      activity.unshift({
        id: createId('act'),
        entityType: endpoint,
        entityId: id,
        action: 'updated',
        actor: person(0),
        summary: `${person(0).name} updated this record`,
        occurredAt: nowIso(),
      })
      store.activity[id] = activity
      return ok(updated)
    },

    async delete(id) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.delete(`${endpoint}/${id}`) as any
      }
      await mockLatency(null)
      const index = store.items.findIndex(x => x.id === id)
      if (index < 0) throw createError({ statusCode: 404, statusMessage: 'Not found' })
      store.items.splice(index, 1)
      delete store.comments[id]
      delete store.activity[id]
      delete store.attachments[id]
      return ok({ id })
    },

    async deleteMany(ids) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.delete(endpoint, { body: { ids } }) as any
      }
      await mockLatency(null)
      const idSet = new Set(ids)
      store.items = store.items.filter(item => !idSet.has(item.id))
      for (const id of ids) {
        delete store.comments[id]
        delete store.activity[id]
        delete store.attachments[id]
      }
      return ok({ ids })
    },

    async transitionStage(id, stage) {
      return await this.update(id, { stage } as Partial<T>)
    },

    async listByStage(stage, query) {
      return await this.list({ ...query, stage, limit: query?.limit || 10 })
    },

    async listComments(id, query) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.get(ApiEndpoints.COMMENTS('entities', id), { query }) as any
      }
      await mockLatency(null)
      if (!store.comments[id]) store.comments[id] = seedComments('entity', id)
      return applyListQuery(store.comments[id] as any, query, ['body'])
    },

    async addComment(id, body) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.post(ApiEndpoints.COMMENTS('entities', id), { body }) as any
      }
      await mockLatency(null)
      const comment: EntityComment = {
        id: createId('cmt'),
        entityType: 'entity',
        entityId: id,
        body,
        author: person(0),
        createdAt: nowIso(),
      }
      store.comments[id] = [comment, ...(store.comments[id] || seedComments('entity', id))]
      const activity = store.activity[id] || seedActivity('entity', id)
      activity.unshift({
        id: createId('act'),
        entityType: 'entity',
        entityId: id,
        action: 'commented',
        actor: comment.author,
        summary: `${comment.author.name} commented`,
        occurredAt: comment.createdAt,
      })
      store.activity[id] = activity
      return ok(comment)
    },

    async listActivity(id, query) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.get(ApiEndpoints.ACTIVITY('entities', id), { query }) as any
      }
      await mockLatency(null)
      if (!store.activity[id]) store.activity[id] = seedActivity('entity', id)
      return applyListQuery(store.activity[id] as any, query, ['summary', 'action'])
    },

    async listAttachments(id) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.get(ApiEndpoints.ATTACHMENTS('entities', id)) as any
      }
      await mockLatency(null)
      if (!store.attachments[id]) store.attachments[id] = seedAttachments()
      return ok(store.attachments[id]!)
    },

    async replaceAttachments(id, files) {
      if (!getUseMockData()) {
        const api = useApi()
        return await api.put(ApiEndpoints.ATTACHMENTS('entities', id), { files }) as any
      }
      await mockLatency(null)
      store.attachments[id] = [...files]
      const index = store.items.findIndex(x => x.id === id)
      if (index >= 0) {
        store.items[index] = {
          ...store.items[index]!,
          attachmentCount: files.length,
          updatedAt: nowIso(),
        } as T
      }
      return ok(store.attachments[id]!)
    },
  }
}

export function createStore<T extends { id: string }>(items: T[]): Store<T> {
  return {
    items: [...items],
    comments: {},
    activity: {},
    attachments: {},
  }
}

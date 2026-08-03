import { applyListQuery, createId, mockLatency, nowIso } from '~/mocks/query'
import type {
  CreateDocumentTypeInput,
  CreateRecordAttributeInput,
  CreateRecordTypeInput,
  DocumentType,
  DocumentTypeQuery,
  RecordAttribute,
  RecordAttributeQuery,
  RecordType,
  RecordTypeQuery,
  UpdateDocumentTypeInput,
  UpdateRecordAttributeInput,
  UpdateRecordTypeInput,
} from '~/types/docetra/configuration'
import {
  defaultRecordTypeFeatures,
  defaultRecordTypeNumbering,
} from '~/types/docetra/configuration'
import type {
  DocumentTypeRepository,
  RecordAttributeRepository,
  RecordTypeRepository,
} from '~/repositories/contracts/configuration'

const ATTR_KEY = 'docetra:config:record-attributes'
const TYPE_KEY = 'docetra:config:record-types'
const DOC_KEY = 'docetra:config:document-types'

function readStore<T>(key: string, fallback: T[]): T[] {
  if (!import.meta.client) return structuredClone(fallback)
  try {
    const raw = localStorage.getItem(key)
    if (!raw) return structuredClone(fallback)
    return JSON.parse(raw) as T[]
  }
  catch {
    return structuredClone(fallback)
  }
}

function writeStore<T>(key: string, items: T[]) {
  if (!import.meta.client) return
  localStorage.setItem(key, JSON.stringify(items))
}

function seedAttributes(): RecordAttribute[] {
  const now = nowIso()
  return [
    {
      id: 'ra_title',
      label: 'Title',
      code: 'title',
      name: 'Title',
      description: 'Primary record title',
      helpText: 'Short human-readable title',
      dataType: 'short_text',
      placeholder: 'Enter title',
      required: true,
      unique: false,
      readOnly: false,
      searchable: true,
      filterable: true,
      sortable: true,
      showInList: true,
      validation: { minLength: 3, maxLength: 200 },
      options: [],
      visibility: null,
      usedByCount: 2,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_priority',
      label: 'Priority',
      code: 'priority',
      name: 'Priority',
      dataType: 'select',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: true,
      showInList: true,
      options: [
        { id: 'opt_low', label: 'Low', value: 'low', color: '#64748b', active: true, order: 0 },
        { id: 'opt_normal', label: 'Normal', value: 'normal', color: '#2563eb', active: true, order: 1 },
        { id: 'opt_high', label: 'High', value: 'high', color: '#ea580c', active: true, order: 2 },
        { id: 'opt_urgent', label: 'Urgent', value: 'urgent', color: '#dc2626', active: true, order: 3 },
      ],
      visibility: null,
      usedByCount: 1,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_notes',
      label: 'Notes',
      code: 'notes',
      name: 'Notes',
      dataType: 'rich_text',
      required: false,
      unique: false,
      readOnly: false,
      searchable: true,
      filterable: false,
      sortable: false,
      showInList: false,
      options: [],
      visibility: null,
      usedByCount: 1,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_due',
      label: 'Due date',
      code: 'due_at',
      name: 'Due date',
      dataType: 'date',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: true,
      showInList: true,
      validation: { allowPastDate: true, allowFutureDate: true },
      options: [],
      visibility: null,
      usedByCount: 1,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
  ]
}

function seedRecordTypes(): RecordType[] {
  const now = nowIso()
  return [
    {
      id: 'rt_incoming',
      name: 'Incoming Document',
      code: 'incoming',
      description: 'Inbound correspondence workflow',
      icon: 'i-lucide-inbox',
      color: '#2563eb',
      status: 'active',
      features: defaultRecordTypeFeatures(),
      numbering: defaultRecordTypeNumbering('IN'),
      attributes: [
        {
          attributeId: 'ra_title',
          attributeCode: 'title',
          attributeLabel: 'Title',
          dataType: 'short_text',
          required: true,
          readOnly: false,
          visible: true,
          searchable: true,
          filterable: true,
          showInList: true,
          section: 'General',
          order: 0,
        },
        {
          attributeId: 'ra_priority',
          attributeCode: 'priority',
          attributeLabel: 'Priority',
          dataType: 'select',
          required: false,
          readOnly: false,
          visible: true,
          searchable: false,
          filterable: true,
          showInList: true,
          section: 'General',
          order: 1,
        },
      ],
      stages: [
        { id: 'st_intake', name: 'Intake', code: 'intake', color: '#64748b', isInitial: true, isFinal: false, order: 0 },
        { id: 'st_review', name: 'Review', code: 'review', color: '#2563eb', isInitial: false, isFinal: false, order: 1 },
        { id: 'st_done', name: 'Done', code: 'done', color: '#16a34a', isInitial: false, isFinal: true, order: 2 },
      ],
      transitions: [
        { id: 'tr1', fromStageCode: 'intake', toStageCode: 'review' },
        { id: 'tr2', fromStageCode: 'review', toStageCode: 'done' },
      ],
      attributeCount: 2,
      workflowEnabled: true,
      createdAt: now,
      updatedAt: now,
    },
  ]
}

function seedDocumentTypes(): DocumentType[] {
  const now = nowIso()
  return [
    {
      id: 'dt_letter',
      name: 'Official Letter',
      code: 'official_letter',
      description: 'Formal correspondence',
      direction: 'both',
      relatedRecordTypeId: 'rt_incoming',
      relatedRecordTypeName: 'Incoming Document',
      defaultPriority: 'normal',
      defaultConfidentiality: 'internal',
      allowedFileTypes: ['pdf', 'docx'],
      maxFileSizeMb: 25,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'dt_memo',
      name: 'Internal Memo',
      code: 'internal_memo',
      direction: 'internal',
      defaultPriority: 'low',
      defaultConfidentiality: 'internal',
      allowedFileTypes: ['pdf'],
      maxFileSizeMb: 10,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
  ]
}

export function createMockRecordAttributeRepository(): RecordAttributeRepository {
  let items = readStore(ATTR_KEY, seedAttributes())

  const persist = () => writeStore(ATTR_KEY, items)

  return {
    async list(query) {
      const result = applyListQuery(items as unknown as Record<string, unknown>[], {
        ...query,
        dataType: query?.dataType,
      }, ['label', 'code', 'name', 'description'])
      return mockLatency({
        data: result.data as unknown as RecordAttribute[],
        meta: result.meta,
      })
    },
    async getById(id) {
      const found = items.find(i => i.id === id)
      if (!found) throw new Error('Record attribute not found')
      return mockLatency(structuredClone(found))
    },
    async create(input) {
      const now = nowIso()
      const row: RecordAttribute = {
        ...input,
        id: createId('ra'),
        name: input.label,
        usedByCount: 0,
        status: input.status || 'active',
        options: input.options || [],
        createdAt: now,
        updatedAt: now,
      }
      items = [row, ...items]
      persist()
      return mockLatency(structuredClone(row))
    },
    async update(id, input) {
      const idx = items.findIndex(i => i.id === id)
      if (idx < 0) throw new Error('Record attribute not found')
      const next = {
        ...items[idx]!,
        ...input,
        name: input.label ?? items[idx]!.name,
        updatedAt: nowIso(),
      }
      items[idx] = next
      persist()
      return mockLatency(structuredClone(next))
    },
    async duplicate(id) {
      const source = await this.getById(id)
      return this.create({
        ...source,
        label: `${source.label} (Copy)`,
        code: `${source.code}_copy_${Date.now().toString(36).slice(-4)}`,
      })
    },
    async setActive(id, active) {
      return this.update(id, { status: active ? 'active' : 'disabled' })
    },
    async remove(id) {
      items = items.filter(i => i.id !== id)
      persist()
      await mockLatency(undefined)
    },
  }
}

export function createMockRecordTypeRepository(): RecordTypeRepository {
  let items = readStore(TYPE_KEY, seedRecordTypes())
  const persist = () => writeStore(TYPE_KEY, items)

  return {
    async list(query?: RecordTypeQuery) {
      const result = applyListQuery(items as unknown as Record<string, unknown>[], query as any, ['name', 'code', 'description'])
      return mockLatency({
        data: result.data as unknown as RecordType[],
        meta: result.meta,
      })
    },
    async getById(id) {
      const found = items.find(i => i.id === id)
      if (!found) throw new Error('Record type not found')
      return mockLatency(structuredClone(found))
    },
    async create(input: CreateRecordTypeInput) {
      const now = nowIso()
      const row: RecordType = {
        ...input,
        id: createId('rt'),
        status: input.status || 'active',
        features: input.features || defaultRecordTypeFeatures(),
        numbering: input.numbering || defaultRecordTypeNumbering(),
        attributes: input.attributes || [],
        stages: input.stages || [],
        transitions: input.transitions || [],
        attributeCount: (input.attributes || []).length,
        workflowEnabled: input.features?.enableWorkflow ?? true,
        createdAt: now,
        updatedAt: now,
      }
      items = [row, ...items]
      persist()
      return mockLatency(structuredClone(row))
    },
    async update(id, input: UpdateRecordTypeInput) {
      const idx = items.findIndex(i => i.id === id)
      if (idx < 0) throw new Error('Record type not found')
      const prev = items[idx]!
      const next: RecordType = {
        ...prev,
        ...input,
        attributes: input.attributes ?? prev.attributes,
        stages: input.stages ?? prev.stages,
        transitions: input.transitions ?? prev.transitions,
        features: input.features ?? prev.features,
        numbering: input.numbering ?? prev.numbering,
        attributeCount: (input.attributes ?? prev.attributes).length,
        workflowEnabled: (input.features ?? prev.features).enableWorkflow,
        updatedAt: nowIso(),
      }
      items[idx] = next
      persist()
      return mockLatency(structuredClone(next))
    },
    async duplicate(id) {
      const source = await this.getById(id)
      return this.create({
        ...source,
        name: `${source.name} (Copy)`,
        code: `${source.code}_copy_${Date.now().toString(36).slice(-4)}`,
      })
    },
    async setActive(id, active) {
      return this.update(id, { status: active ? 'active' : 'disabled' })
    },
    async remove(id) {
      items = items.filter(i => i.id !== id)
      persist()
      await mockLatency(undefined)
    },
  }
}

export function createMockDocumentTypeRepository(): DocumentTypeRepository {
  let items = readStore(DOC_KEY, seedDocumentTypes())
  const persist = () => writeStore(DOC_KEY, items)

  return {
    async list(query?: DocumentTypeQuery) {
      const result = applyListQuery(items as unknown as Record<string, unknown>[], query as any, ['name', 'code', 'description'])
      return mockLatency({
        data: result.data as unknown as DocumentType[],
        meta: result.meta,
      })
    },
    async getById(id) {
      const found = items.find(i => i.id === id)
      if (!found) throw new Error('Document type not found')
      return mockLatency(structuredClone(found))
    },
    async create(input: CreateDocumentTypeInput) {
      const now = nowIso()
      const row: DocumentType = {
        ...input,
        id: createId('dt'),
        status: input.status || 'active',
        allowedFileTypes: input.allowedFileTypes || [],
        createdAt: now,
        updatedAt: now,
      }
      items = [row, ...items]
      persist()
      return mockLatency(structuredClone(row))
    },
    async update(id, input: UpdateDocumentTypeInput) {
      const idx = items.findIndex(i => i.id === id)
      if (idx < 0) throw new Error('Document type not found')
      const next = { ...items[idx]!, ...input, updatedAt: nowIso() }
      items[idx] = next
      persist()
      return mockLatency(structuredClone(next))
    },
    async duplicate(id) {
      const source = await this.getById(id)
      return this.create({
        ...source,
        name: `${source.name} (Copy)`,
        code: `${source.code}_copy_${Date.now().toString(36).slice(-4)}`,
      })
    },
    async setActive(id, active) {
      return this.update(id, { status: active ? 'active' : 'disabled' })
    },
    async remove(id) {
      items = items.filter(i => i.id !== id)
      persist()
      await mockLatency(undefined)
    },
  }
}

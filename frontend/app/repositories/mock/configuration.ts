import type { RecordAttributeRepository, RecordTypeRepository } from '~/repositories/contracts/configuration'
import type {
  CreateRecordAttributeInput,
  CreateRecordTypeInput,
  RecordAttribute,
  RecordType,
  UpdateRecordAttributeInput,
  UpdateRecordTypeInput,
} from '~/types/docetra/configuration'
import { defaultRecordTypeFeatures, defaultRecordTypeNumbering } from '~/types/docetra/configuration'
import { applyListQuery, mockLatency, nowIso } from '~/mocks/query'
import { createClientId } from '~/utils/client-id'

const ATTRIBUTE_KEY = 'docetra:mock:record-attributes:v1'
const RECORD_TYPE_KEY = 'docetra:mock:record-types:v1'

function readRows<T>(key: string, fallback: T[]): T[] {
  if (!import.meta.client) return structuredClone(fallback)
  try {
    const raw = localStorage.getItem(key)
    return raw ? JSON.parse(raw) as T[] : structuredClone(fallback)
  }
  catch {
    return structuredClone(fallback)
  }
}

function writeRows<T>(key: string, rows: T[]) {
  if (import.meta.client) localStorage.setItem(key, JSON.stringify(rows))
}

function seedAttributes(): RecordAttribute[] {
  const now = nowIso()
  return [
    { id: 'ra_title', label: 'Title', name: 'Title', code: 'title', dataType: 'short_text', required: true, unique: false, readOnly: false, searchable: true, filterable: true, sortable: true, showInList: true, usedByCount: 4, status: 'active', createdAt: now, updatedAt: now },
    { id: 'ra_priority', label: 'Priority', name: 'Priority', code: 'priority', dataType: 'select', required: false, unique: false, readOnly: false, searchable: false, filterable: true, sortable: true, showInList: true, usedByCount: 3, status: 'active', options: [], createdAt: now, updatedAt: now },
    { id: 'ra_notes', label: 'Notes', name: 'Notes', code: 'notes', dataType: 'rich_text', required: false, unique: false, readOnly: false, searchable: true, filterable: false, sortable: false, showInList: false, usedByCount: 2, status: 'active', createdAt: now, updatedAt: now },
  ]
}

function seedRecordTypes(): RecordType[] {
  const now = nowIso()
  const seeds = [
    ['rt_incoming', 'Incoming Document', 'incoming', 'IN'],
    ['rt_outgoing', 'Outgoing Document', 'outgoing', 'OUT'],
    ['rt_document', 'Document', 'document', 'DOC'],
    ['rt_master_list', 'Master List Request', 'master_list', 'MLR'],
  ] as const
  return seeds.map(([id, name, code, prefix]) => ({
    id,
    name,
    code,
    description: `${name} workflow`,
    status: 'active',
    features: defaultRecordTypeFeatures(),
    numbering: defaultRecordTypeNumbering(prefix),
    attributes: [],
    stages: [],
    transitions: [],
    attributeCount: 0,
    workflowEnabled: true,
    createdAt: now,
    updatedAt: now,
  }))
}

export function createMockRecordAttributeRepository(): RecordAttributeRepository {
  let rows = readRows(ATTRIBUTE_KEY, seedAttributes())
  return {
    async list(query) {
      await mockLatency(null)
      return applyListQuery(rows as unknown as Record<string, unknown>[], query as any, ['label', 'name', 'code']) as unknown as Awaited<ReturnType<RecordAttributeRepository['list']>>
    },
    async getById(id) {
      await mockLatency(null)
      const row = rows.find(item => item.id === id)
      if (!row) throw new Error('Record attribute not found')
      return structuredClone(row)
    },
    async create(input: CreateRecordAttributeInput) {
      const now = nowIso()
      const row = { ...input, id: createClientId('ra'), name: input.label, usedByCount: 0, status: input.status || 'active', createdAt: now, updatedAt: now } as RecordAttribute
      rows.unshift(row)
      writeRows(ATTRIBUTE_KEY, rows)
      return mockLatency(structuredClone(row))
    },
    async update(id, input: UpdateRecordAttributeInput) {
      const index = rows.findIndex(item => item.id === id)
      if (index < 0) throw new Error('Record attribute not found')
      rows[index] = { ...rows[index]!, ...input, name: input.label || rows[index]!.name, updatedAt: nowIso() }
      writeRows(ATTRIBUTE_KEY, rows)
      return mockLatency(structuredClone(rows[index]!))
    },
    async duplicate(id) {
      const source = await this.getById(id)
      return this.create({ ...source, label: `${source.label} Copy`, code: `${source.code}_copy` })
    },
    setActive(id, active) { return this.update(id, { status: active ? 'active' : 'disabled' }) },
    async remove(id) { rows = rows.filter(item => item.id !== id); writeRows(ATTRIBUTE_KEY, rows); await mockLatency(null) },
  }
}

export function createMockRecordTypeRepository(): RecordTypeRepository {
  let rows = readRows(RECORD_TYPE_KEY, seedRecordTypes())
  return {
    async list(query) {
      await mockLatency(null)
      return applyListQuery(rows as unknown as Record<string, unknown>[], query as any, ['name', 'code', 'description']) as unknown as Awaited<ReturnType<RecordTypeRepository['list']>>
    },
    async getById(id) {
      await mockLatency(null)
      const row = rows.find(item => item.id === id)
      if (!row) throw new Error('Record type not found')
      return structuredClone(row)
    },
    async create(input: CreateRecordTypeInput) {
      const now = nowIso()
      const row = { ...input, id: createClientId('rt'), status: input.status || 'active', features: input.features || defaultRecordTypeFeatures(), numbering: input.numbering || defaultRecordTypeNumbering(), attributes: input.attributes || [], stages: input.stages || [], transitions: input.transitions || [], attributeCount: input.attributes?.length || 0, workflowEnabled: input.features?.enableWorkflow ?? true, createdAt: now, updatedAt: now } as RecordType
      rows.unshift(row)
      writeRows(RECORD_TYPE_KEY, rows)
      return mockLatency(structuredClone(row))
    },
    async update(id, input: UpdateRecordTypeInput) {
      const index = rows.findIndex(item => item.id === id)
      if (index < 0) throw new Error('Record type not found')
      const previous = rows[index]!
      rows[index] = { ...previous, ...input, attributeCount: (input.attributes || previous.attributes).length, workflowEnabled: (input.features || previous.features).enableWorkflow, updatedAt: nowIso() }
      writeRows(RECORD_TYPE_KEY, rows)
      return mockLatency(structuredClone(rows[index]!))
    },
    async duplicate(id) {
      const source = await this.getById(id)
      return this.create({ ...source, name: `${source.name} Copy`, code: `${source.code}_copy` })
    },
    setActive(id, active) { return this.update(id, { status: active ? 'active' : 'disabled' }) },
    async remove(id) { rows = rows.filter(item => item.id !== id); writeRows(RECORD_TYPE_KEY, rows); await mockLatency(null) },
  }
}

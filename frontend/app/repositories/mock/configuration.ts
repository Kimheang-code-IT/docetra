import type { RecordAttributeRepository, RecordTypeRepository } from '~/repositories/contracts/configuration'
import type {
  CreateRecordAttributeInput,
  CreateRecordTypeInput,
  RecordAttribute,
  RecordType,
  RecordTypeAttribute,
  UpdateRecordAttributeInput,
  UpdateRecordTypeInput,
} from '~/types/docetra/configuration'
import { defaultRecordTypeFeatures, defaultRecordTypeNumbering } from '~/types/docetra/configuration'
import { applyListQuery, mockLatency, nowIso } from '~/mocks/query'
import { createClientId } from '~/utils/client-id'

const ATTRIBUTE_KEY = 'docetra:mock:record-attributes:v2'
const RECORD_TYPE_KEY = 'docetra:mock:record-types:v2'
/** One-time: drop legacy v1 keys and empty pre-assignment v2 caches. */
const CONFIG_MIGRATION_KEY = 'docetra:mock:config-migration:v2-assigned-attrs'

const LEGACY_CONFIG_KEYS = [
  'docetra:mock:record-attributes:v1',
  'docetra:mock:record-types:v1',
]

function clearLegacyConfigStorage() {
  if (!import.meta.client) return
  for (const key of LEGACY_CONFIG_KEYS) {
    localStorage.removeItem(key)
  }
  // Force reseed once so types ship with assigned attributes (empty v2 from early drafts).
  if (!localStorage.getItem(CONFIG_MIGRATION_KEY)) {
    localStorage.removeItem(ATTRIBUTE_KEY)
    localStorage.removeItem(RECORD_TYPE_KEY)
    localStorage.setItem(CONFIG_MIGRATION_KEY, '1')
  }
}

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

function toAssignment(attr: RecordAttribute, order: number, section = 'General'): RecordTypeAttribute {
  return {
    attributeId: attr.id,
    attributeCode: attr.code,
    attributeLabel: attr.label,
    dataType: attr.dataType,
    required: attr.required,
    readOnly: attr.readOnly,
    visible: true,
    searchable: attr.searchable,
    filterable: attr.filterable,
    showInList: attr.showInList,
    section,
    order,
  }
}

function seedAttributes(): RecordAttribute[] {
  const now = nowIso()
  return [
    {
      id: 'ra_priority',
      label: 'Priority',
      name: 'Priority',
      code: 'priority',
      dataType: 'select',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: true,
      showInList: true,
      usedByCount: 0,
      status: 'active',
      options: [
        { id: 'opt_low', label: 'Low', value: 'low', active: true, order: 0 },
        { id: 'opt_med', label: 'Medium', value: 'medium', active: true, order: 1 },
        { id: 'opt_high', label: 'High', value: 'high', active: true, order: 2 },
      ],
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_notes',
      label: 'Notes',
      name: 'Notes',
      code: 'notes',
      dataType: 'long_text',
      required: false,
      unique: false,
      readOnly: false,
      searchable: true,
      filterable: false,
      sortable: false,
      showInList: false,
      usedByCount: 0,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_due_date',
      label: 'Due date',
      name: 'Due date',
      code: 'due_date',
      dataType: 'date',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: true,
      showInList: true,
      usedByCount: 0,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_external_ref',
      label: 'External reference',
      name: 'External reference',
      code: 'external_ref',
      dataType: 'short_text',
      required: false,
      unique: false,
      readOnly: false,
      searchable: true,
      filterable: true,
      sortable: true,
      showInList: true,
      usedByCount: 0,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_confidential',
      label: 'Confidential',
      name: 'Confidential',
      code: 'confidential',
      dataType: 'boolean',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: false,
      showInList: true,
      usedByCount: 0,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_amount',
      label: 'Amount',
      name: 'Amount',
      code: 'amount',
      dataType: 'decimal',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: true,
      showInList: true,
      usedByCount: 0,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
  ]
}

function defaultStages() {
  return [
    { id: 'stg_intake', name: 'Intake', code: 'intake', isInitial: true, isFinal: false, order: 0, color: '#64748b' },
    { id: 'stg_review', name: 'Review', code: 'review', isInitial: false, isFinal: false, order: 1, color: '#2563eb' },
    { id: 'stg_approval', name: 'Approval', code: 'approval', isInitial: false, isFinal: false, order: 2, color: '#d97706' },
    { id: 'stg_completed', name: 'Completed', code: 'completed', isInitial: false, isFinal: true, order: 3, color: '#16a34a' },
  ]
}

function seedRecordTypes(attrs: RecordAttribute[]): RecordType[] {
  const now = nowIso()
  const byId = Object.fromEntries(attrs.map(a => [a.id, a])) as Record<string, RecordAttribute>
  const pick = (...ids: string[]) =>
    ids
      .map((id, order) => byId[id] ? toAssignment(byId[id]!, order) : null)
      .filter(Boolean) as RecordTypeAttribute[]

  const seeds: Array<{
    id: string
    name: string
    code: string
    prefix: string
    attributeIds: string[]
  }> = [
    {
      id: 'rt_incoming',
      name: 'Incoming Document',
      code: 'incoming',
      prefix: 'IN',
      attributeIds: ['ra_priority', 'ra_external_ref', 'ra_due_date', 'ra_notes', 'ra_confidential'],
    },
    {
      id: 'rt_outgoing',
      name: 'Outgoing Document',
      code: 'outgoing',
      prefix: 'OUT',
      attributeIds: ['ra_priority', 'ra_external_ref', 'ra_due_date', 'ra_notes'],
    },
    {
      id: 'rt_document',
      name: 'Document',
      code: 'document',
      prefix: 'DOC',
      attributeIds: ['ra_priority', 'ra_notes', 'ra_confidential', 'ra_amount'],
    },
    {
      id: 'rt_master_list',
      name: 'Master List Request',
      code: 'master_list',
      prefix: 'MLR',
      attributeIds: ['ra_priority', 'ra_due_date', 'ra_external_ref', 'ra_notes', 'ra_amount'],
    },
  ]

  return seeds.map(({ id, name, code, prefix, attributeIds }) => ({
    id,
    name,
    code,
    description: `${name} workflow`,
    status: 'active',
    features: defaultRecordTypeFeatures(),
    numbering: defaultRecordTypeNumbering(prefix),
    attributes: pick(...attributeIds),
    stages: defaultStages(),
    transitions: [],
    attributeCount: attributeIds.length,
    workflowEnabled: true,
    createdAt: now,
    updatedAt: now,
  }))
}

/** Shared in-memory store so type updates can sync attribute usedByCount. */
clearLegacyConfigStorage()
const seedAttrs = seedAttributes()
let attributeRows = readRows(ATTRIBUTE_KEY, seedAttrs)
let typeRows = readRows(RECORD_TYPE_KEY, seedRecordTypes(seedAttrs))

function recalculateUsedByCounts() {
  const counts = new Map<string, number>()
  for (const type of typeRows) {
    for (const attr of type.attributes || []) {
      counts.set(attr.attributeId, (counts.get(attr.attributeId) || 0) + 1)
    }
  }
  attributeRows = attributeRows.map(attr => ({
    ...attr,
    usedByCount: counts.get(attr.id) || 0,
  }))
  writeRows(ATTRIBUTE_KEY, attributeRows)
}

// Ensure seeded counts are consistent on first load
recalculateUsedByCounts()

export function createMockRecordAttributeRepository(): RecordAttributeRepository {
  return {
    async list(query) {
      await mockLatency(null)
      const q = { ...(query || {}) } as Record<string, unknown>
      const unused = q.unused === true || q.unused === 'true'
      delete q.unused
      let filtered = attributeRows as unknown as Record<string, unknown>[]
      if (unused) {
        filtered = filtered.filter(row => !Number(row.usedByCount || 0))
      }
      return applyListQuery(filtered, q as any, ['label', 'name', 'code']) as unknown as Awaited<ReturnType<RecordAttributeRepository['list']>>
    },
    async getById(id) {
      await mockLatency(null)
      const row = attributeRows.find(item => item.id === id)
      if (!row) throw new Error('Record attribute not found')
      return structuredClone(row)
    },
    async create(input: CreateRecordAttributeInput) {
      const now = nowIso()
      const row = {
        ...input,
        id: createClientId('ra'),
        name: input.label,
        usedByCount: 0,
        status: input.status || 'active',
        createdAt: now,
        updatedAt: now,
      } as RecordAttribute
      attributeRows.unshift(row)
      writeRows(ATTRIBUTE_KEY, attributeRows)
      return mockLatency(structuredClone(row))
    },
    async update(id, input: UpdateRecordAttributeInput) {
      const index = attributeRows.findIndex(item => item.id === id)
      if (index < 0) throw new Error('Record attribute not found')
      attributeRows[index] = {
        ...attributeRows[index]!,
        ...input,
        name: input.label || attributeRows[index]!.name,
        updatedAt: nowIso(),
      }
      writeRows(ATTRIBUTE_KEY, attributeRows)
      return mockLatency(structuredClone(attributeRows[index]!))
    },
    async duplicate(id) {
      const source = await this.getById(id)
      return this.create({ ...source, label: `${source.label} Copy`, code: `${source.code}_copy` })
    },
    setActive(id, active) { return this.update(id, { status: active ? 'active' : 'disabled' }) },
    async remove(id) {
      attributeRows = attributeRows.filter(item => item.id !== id)
      writeRows(ATTRIBUTE_KEY, attributeRows)
      await mockLatency(null)
    },
  }
}

export function createMockRecordTypeRepository(): RecordTypeRepository {
  return {
    async list(query) {
      await mockLatency(null)
      return applyListQuery(typeRows as unknown as Record<string, unknown>[], query as any, ['name', 'code', 'description']) as unknown as Awaited<ReturnType<RecordTypeRepository['list']>>
    },
    async getById(id) {
      await mockLatency(null)
      const row = typeRows.find(item => item.id === id)
      if (!row) throw new Error('Record type not found')
      return structuredClone(row)
    },
    async create(input: CreateRecordTypeInput) {
      const now = nowIso()
      const attributes = input.attributes || []
      const row = {
        ...input,
        id: createClientId('rt'),
        status: input.status || 'active',
        features: input.features || defaultRecordTypeFeatures(),
        numbering: input.numbering || defaultRecordTypeNumbering(),
        attributes,
        stages: input.stages || [],
        transitions: input.transitions || [],
        attributeCount: attributes.length,
        workflowEnabled: input.features?.enableWorkflow ?? true,
        createdAt: now,
        updatedAt: now,
      } as RecordType
      typeRows.unshift(row)
      writeRows(RECORD_TYPE_KEY, typeRows)
      recalculateUsedByCounts()
      return mockLatency(structuredClone(row))
    },
    async update(id, input: UpdateRecordTypeInput) {
      const index = typeRows.findIndex(item => item.id === id)
      if (index < 0) throw new Error('Record type not found')
      const previous = typeRows[index]!
      const attributes = input.attributes ?? previous.attributes
      typeRows[index] = {
        ...previous,
        ...input,
        attributes,
        attributeCount: attributes.length,
        workflowEnabled: (input.features || previous.features).enableWorkflow,
        updatedAt: nowIso(),
      }
      writeRows(RECORD_TYPE_KEY, typeRows)
      recalculateUsedByCounts()
      return mockLatency(structuredClone(typeRows[index]!))
    },
    async duplicate(id) {
      const source = await this.getById(id)
      return this.create({ ...source, name: `${source.name} Copy`, code: `${source.code}_copy` })
    },
    setActive(id, active) { return this.update(id, { status: active ? 'active' : 'disabled' }) },
    async remove(id) {
      typeRows = typeRows.filter(item => item.id !== id)
      writeRows(RECORD_TYPE_KEY, typeRows)
      recalculateUsedByCounts()
      await mockLatency(null)
    },
  }
}

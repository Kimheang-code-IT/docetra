import type { ConfigurationDiscussionRepository, RecordAttributeRepository, RecordTypeRepository } from '~/repositories/contracts/configuration'
import type { ActivityEvent, EntityComment } from '~/types/docetra/common'
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
import { applyListQuery, createId, mockLatency, nowIso, ok } from '~/mocks/query'
import { person, seedActivity, seedComments } from '~/mocks/seed'
import { createClientId } from '~/utils/client-id'

const ATTRIBUTE_KEY = 'docetra:mock:record-attributes:v2'
const RECORD_TYPE_KEY = 'docetra:mock:record-types:v2'
/** One-time: drop legacy v1 keys and empty pre-assignment v2 caches. */
const CONFIG_MIGRATION_KEY = 'docetra:mock:config-migration:v2-assigned-attrs'
const RECORD_BACKED_TYPES_MIGRATION_KEY = 'docetra:mock:config-migration:v3-record-backed-types'
const RECORD_STAGE_ALIGNMENT_MIGRATION_KEY = 'docetra:mock:config-migration:v4-record-stage-alignment'
const REMOVE_DEMO_FORM_FIELDS_MIGRATION_KEY = 'docetra:mock:config-migration:v5-remove-demo-form-fields'
const DYNAMIC_FIELD_UI_TEST_MIGRATION_KEY = 'docetra:mock:config-migration:v6-dynamic-field-ui-test'
const REMOVED_DEFAULT_FIELD_CODES = new Set(['priority', 'due_date', 'notes', 'confidential'])

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

function pickAssignments(
  byId: Record<string, RecordAttribute>,
  specs: Array<{ id: string, section?: string }>,
): RecordTypeAttribute[] {
  return specs
    .map((spec, order) => {
      const attr = byId[spec.id]
      return attr ? toAssignment(attr, order, spec.section ?? 'General') : null
    })
    .filter(Boolean) as RecordTypeAttribute[]
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
    {
      id: 'ra_tags',
      label: 'Tags',
      name: 'Tags',
      code: 'tags',
      dataType: 'multi_select',
      required: false,
      unique: false,
      readOnly: false,
      searchable: true,
      filterable: true,
      sortable: false,
      showInList: true,
      usedByCount: 0,
      status: 'active',
      options: [
        { id: 'opt_tag_internal', label: 'Internal', value: 'internal', active: true, order: 0 },
        { id: 'opt_tag_external', label: 'External', value: 'external', active: true, order: 1 },
        { id: 'opt_tag_legal', label: 'Legal', value: 'legal', active: true, order: 2 },
        { id: 'opt_tag_finance', label: 'Finance', value: 'finance', active: true, order: 3 },
      ],
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_contact_email',
      label: 'Contact email',
      name: 'Contact email',
      code: 'contact_email',
      dataType: 'email',
      required: false,
      unique: false,
      readOnly: false,
      searchable: true,
      filterable: false,
      sortable: false,
      showInList: false,
      usedByCount: 0,
      status: 'active',
      placeholder: 'name@organization.gov.kh',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_source_url',
      label: 'Source URL',
      name: 'Source URL',
      code: 'source_url',
      dataType: 'url',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: false,
      sortable: false,
      showInList: false,
      usedByCount: 0,
      status: 'active',
      placeholder: 'https://',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_page_count',
      label: 'Page count',
      name: 'Page count',
      code: 'page_count',
      dataType: 'integer',
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
      id: 'ra_budget',
      label: 'Budget',
      name: 'Budget',
      code: 'budget',
      dataType: 'currency',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: true,
      showInList: false,
      usedByCount: 0,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_review_time',
      label: 'Review time',
      name: 'Review time',
      code: 'review_time',
      dataType: 'datetime',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: true,
      showInList: false,
      usedByCount: 0,
      status: 'active',
      createdAt: now,
      updatedAt: now,
    },
    {
      id: 'ra_meeting_format',
      label: 'Meeting format',
      name: 'Meeting format',
      code: 'meeting_format',
      dataType: 'select',
      required: false,
      unique: false,
      readOnly: false,
      searchable: false,
      filterable: true,
      sortable: false,
      showInList: true,
      usedByCount: 0,
      status: 'active',
      options: [
        { id: 'opt_fmt_in_person', label: 'In person', value: 'in_person', active: true, order: 0 },
        { id: 'opt_fmt_online', label: 'Online', value: 'online', active: true, order: 1 },
        { id: 'opt_fmt_hybrid', label: 'Hybrid', value: 'hybrid', active: true, order: 2 },
      ],
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

function recordDocumentStages() {
  const rows = [
    ['created', 'Created', '#64748b'],
    ['record_created', 'Record Created', '#0284c7'],
    ['observation_note', 'Observation Note', '#d97706'],
    ['waiting_related_document', 'Waiting Related Document', '#d97706'],
    ['submitted_director', 'Submitted to Director', '#2563eb'],
    ['submitted_ddg', 'Submitted to DDG', '#2563eb'],
    ['submitted_dg', 'Submitted to DG', '#2563eb'],
    ['further_measures', 'Further Measures', '#0284c7'],
    ['reply', 'Reply', '#16a34a'],
    ['finished_final', 'Finished / Final', '#16a34a'],
  ] as const
  return rows.map(([code, name, color], order) => ({
    id: `stg_${code}`,
    name,
    code,
    color,
    isInitial: order === 0,
    isFinal: order === rows.length - 1,
    order,
  }))
}

function seedRecordTypes(attrs: RecordAttribute[]): RecordType[] {
  const now = nowIso()
  const byId = Object.fromEntries(attrs.map(a => [a.id, a])) as Record<string, RecordAttribute>

  const seeds: Array<{
    id: string
    name: string
    code: string
    prefix: string
    assignments: Array<{ id: string, section?: string }>
  }> = [
    {
      id: 'rt_incoming',
      name: 'Incoming Document',
      code: 'incoming',
      prefix: 'IN',
      assignments: [
        { id: 'ra_external_ref', section: 'Reference' },
        { id: 'ra_contact_email', section: 'Reference' },
        { id: 'ra_priority', section: 'Processing' },
        { id: 'ra_due_date', section: 'Processing' },
        { id: 'ra_confidential', section: 'Processing' },
        { id: 'ra_notes', section: 'Processing' },
      ],
    },
    {
      id: 'rt_outgoing',
      name: 'Outgoing Document',
      code: 'outgoing',
      prefix: 'OUT',
      assignments: [
        { id: 'ra_external_ref', section: 'Reference' },
        { id: 'ra_source_url', section: 'Reference' },
        { id: 'ra_priority', section: 'Processing' },
        { id: 'ra_due_date', section: 'Processing' },
        { id: 'ra_notes', section: 'Processing' },
      ],
    },
    {
      id: 'rt_document',
      name: 'Document',
      code: 'document',
      prefix: 'DOC',
      assignments: [
        { id: 'ra_amount', section: 'Financial' },
        { id: 'ra_budget', section: 'Financial' },
        { id: 'ra_priority', section: 'Metadata' },
        { id: 'ra_page_count', section: 'Metadata' },
        { id: 'ra_tags', section: 'Metadata' },
        { id: 'ra_notes', section: 'Metadata' },
      ],
    },
    {
      id: 'rt_master_list',
      name: 'Master List Request',
      code: 'master_list',
      prefix: 'MLR',
      assignments: [
        { id: 'ra_external_ref', section: 'Reference' },
        { id: 'ra_amount', section: 'Financial' },
        { id: 'ra_priority', section: 'Processing' },
        { id: 'ra_due_date', section: 'Processing' },
        { id: 'ra_confidential', section: 'Processing' },
        { id: 'ra_notes', section: 'Processing' },
      ],
    },
    {
      id: 'rt_meeting',
      name: 'Meeting',
      code: 'meeting',
      prefix: 'MTG',
      assignments: [
        { id: 'ra_meeting_format', section: 'Schedule' },
        { id: 'ra_review_time', section: 'Schedule' },
        { id: 'ra_priority', section: 'Notes' },
        { id: 'ra_notes', section: 'Notes' },
      ],
    },
    {
      id: 'rt_meeting_topic',
      name: 'Meeting Topic',
      code: 'meeting_topic',
      prefix: 'TOP',
      assignments: [
        { id: 'ra_priority', section: 'Planning' },
        { id: 'ra_due_date', section: 'Planning' },
        { id: 'ra_tags', section: 'Planning' },
        { id: 'ra_notes', section: 'Planning' },
      ],
    },
  ]

  return seeds.map(({ id, name, code, prefix, assignments }) => ({
    id,
    name,
    code,
    description: `${name} workflow`,
    status: 'active',
    features: defaultRecordTypeFeatures(),
    numbering: defaultRecordTypeNumbering(prefix),
    attributes: pickAssignments(byId, assignments),
    stages: ['incoming', 'outgoing', 'document', 'master_list'].includes(code)
      ? recordDocumentStages()
      : defaultStages(),
    transitions: [],
    attributeCount: assignments.length,
    workflowEnabled: true,
    createdAt: now,
    updatedAt: now,
  }))
}

/** Shared in-memory store so type updates can sync attribute usedByCount. */
clearLegacyConfigStorage()
const seedAttrs = seedAttributes()
let attributeRows = readRows(ATTRIBUTE_KEY, seedAttrs)
const seededTypeRows = seedRecordTypes(seedAttrs)
let typeRows = readRows(RECORD_TYPE_KEY, seededTypeRows)

if (import.meta.client && !localStorage.getItem(RECORD_BACKED_TYPES_MIGRATION_KEY)) {
  const existingCodes = new Set(typeRows.map(type => type.code))
  typeRows = [
    ...typeRows,
    ...seededTypeRows.filter(type => !existingCodes.has(type.code)),
  ]
  writeRows(RECORD_TYPE_KEY, typeRows)
  localStorage.setItem(RECORD_BACKED_TYPES_MIGRATION_KEY, '1')
}

if (import.meta.client && !localStorage.getItem(RECORD_STAGE_ALIGNMENT_MIGRATION_KEY)) {
  const legacyDefaultCodes = defaultStages().map(stage => stage.code).join('|')
  typeRows = typeRows.map((type) => {
    const isDocumentType = ['incoming', 'outgoing', 'document', 'master_list'].includes(type.code)
    const currentCodes = [...(type.stages || [])]
      .sort((a, b) => a.order - b.order)
      .map(stage => stage.code)
      .join('|')
    return isDocumentType && currentCodes === legacyDefaultCodes
      ? { ...type, stages: recordDocumentStages() }
      : type
  })
  writeRows(RECORD_TYPE_KEY, typeRows)
  localStorage.setItem(RECORD_STAGE_ALIGNMENT_MIGRATION_KEY, '1')
}

// Remove obsolete demo assignments from existing mock Record Types without
// deleting the Attribute Catalog entries. Users may assign them again later.
if (import.meta.client && !localStorage.getItem(REMOVE_DEMO_FORM_FIELDS_MIGRATION_KEY)) {
  typeRows = typeRows.map((type) => {
    const attributes = (type.attributes || [])
      .filter(attribute => !REMOVED_DEFAULT_FIELD_CODES.has(attribute.attributeCode))
      .map((attribute, order) => ({ ...attribute, order }))
    return {
      ...type,
      attributes,
      attributeCount: attributes.length,
      updatedAt: nowIso(),
    }
  })
  writeRows(RECORD_TYPE_KEY, typeRows)
  localStorage.setItem(REMOVE_DEMO_FORM_FIELDS_MIGRATION_KEY, '1')
}

// Seed richer dynamic-field assignments + catalog entries for manual UI testing.
if (import.meta.client && !localStorage.getItem(DYNAMIC_FIELD_UI_TEST_MIGRATION_KEY)) {
  const catalogById = new Map(attributeRows.map(row => [row.id, row]))
  for (const row of seedAttributes()) {
    if (!catalogById.has(row.id)) {
      attributeRows.push(row)
      catalogById.set(row.id, row)
    }
  }
  writeRows(ATTRIBUTE_KEY, attributeRows)

  const seededAssignments = Object.fromEntries(
    seedRecordTypes(attributeRows).map(type => [type.id, type]),
  )
  typeRows = typeRows.map((type) => {
    const seeded = seededAssignments[type.id]
    if (!seeded) return type
    return {
      ...type,
      attributes: seeded.attributes,
      attributeCount: seeded.attributeCount,
      updatedAt: nowIso(),
    }
  })
  writeRows(RECORD_TYPE_KEY, typeRows)
  localStorage.setItem(DYNAMIC_FIELD_UI_TEST_MIGRATION_KEY, '1')
}

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

function createMockConfigurationDiscussion(entityType: string) {
  const comments: Record<string, EntityComment[]> = {}
  const activity: Record<string, ActivityEvent[]> = {}

  function track(id: string, action: string, summary: string) {
    const actor = person(0)
    activity[id] = [{
      id: createId('act'),
      entityType,
      entityId: id,
      action,
      actor,
      summary,
      occurredAt: nowIso(),
    }, ...(activity[id] || [])]
  }

  const repository: ConfigurationDiscussionRepository = {
    async listComments(id, query) {
      await mockLatency(null)
      comments[id] ||= seedComments(entityType, id)
      return applyListQuery(
        comments[id] as unknown as Record<string, unknown>[],
        query,
        ['body'],
      ) as unknown as Awaited<ReturnType<ConfigurationDiscussionRepository['listComments']>>
    },
    async addComment(id, body, author) {
      await mockLatency(null)
      const comment: EntityComment = {
        id: createId('cmt'),
        entityType,
        entityId: id,
        body,
        author: author || person(0),
        createdAt: nowIso(),
      }
      comments[id] = [comment, ...(comments[id] || [])]
      track(id, 'commented', `${comment.author.name} commented`)
      return ok(structuredClone(comment))
    },
    async updateComment(id, commentId, body) {
      await mockLatency(null)
      comments[id] ||= seedComments(entityType, id)
      const index = comments[id].findIndex(comment => comment.id === commentId)
      if (index < 0) throw new Error('Comment not found')
      const comment = { ...comments[id][index]!, body, editedAt: nowIso() }
      comments[id][index] = comment
      track(id, 'comment_updated', `${comment.author.name} edited a comment`)
      return ok(structuredClone(comment))
    },
    async deleteComment(id, commentId) {
      await mockLatency(null)
      comments[id] ||= seedComments(entityType, id)
      const index = comments[id].findIndex(comment => comment.id === commentId)
      if (index < 0) throw new Error('Comment not found')
      comments[id].splice(index, 1)
      track(id, 'comment_deleted', `${person(0).name} deleted a comment`)
      return ok({ id: commentId })
    },
    async listActivity(id, query) {
      await mockLatency(null)
      activity[id] ||= seedActivity(entityType, id)
      return applyListQuery(
        activity[id] as unknown as Record<string, unknown>[],
        query,
        ['summary', 'action'],
      ) as unknown as Awaited<ReturnType<ConfigurationDiscussionRepository['listActivity']>>
    },
  }

  return {
    repository,
    track,
    commentCount: (id: string) => comments[id]?.length || 0,
    clear(id: string) {
      delete comments[id]
      delete activity[id]
    },
  }
}

export function createMockRecordAttributeRepository(): RecordAttributeRepository {
  const discussion = createMockConfigurationDiscussion('record_attribute')
  return {
    ...discussion.repository,
    async list(query) {
      await mockLatency(null)
      const q = { ...(query || {}) } as Record<string, unknown>
      const unused = q.unused === true || q.unused === 'true'
      delete q.unused
      let filtered = attributeRows.map(row => ({
        ...row,
        updatedBy: row.updatedBy || person(0),
        commentCount: discussion.commentCount(row.id),
      })) as unknown as Record<string, unknown>[]
      if (unused) {
        filtered = filtered.filter(row => !Number(row.usedByCount || 0))
      }
      return applyListQuery(filtered, q as any, ['label', 'name', 'code']) as unknown as Awaited<ReturnType<RecordAttributeRepository['list']>>
    },
    async getById(id) {
      await mockLatency(null)
      const row = attributeRows.find(item => item.id === id)
      if (!row) throw new Error('Record attribute not found')
      return structuredClone({ ...row, updatedBy: row.updatedBy || person(0) })
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
        createdBy: person(0),
        updatedBy: person(0),
      } as RecordAttribute
      attributeRows.unshift(row)
      discussion.track(row.id, 'created', `${person(0).name} created this attribute`)
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
        updatedBy: person(0),
      }
      const nextStatus = input.status
      discussion.track(
        id,
        nextStatus === 'active' ? 'activated' : nextStatus === 'disabled' ? 'deactivated' : 'updated',
        nextStatus === 'active'
          ? `${person(0).name} activated this attribute`
          : nextStatus === 'disabled'
            ? `${person(0).name} deactivated this attribute`
            : `${person(0).name} updated this attribute`,
      )
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
      discussion.clear(id)
      writeRows(ATTRIBUTE_KEY, attributeRows)
      await mockLatency(null)
    },
    async removeMany(ids) {
      const idSet = new Set(ids)
      attributeRows = attributeRows.filter(item => !idSet.has(item.id))
      ids.forEach(id => discussion.clear(id))
      writeRows(ATTRIBUTE_KEY, attributeRows)
      await mockLatency(null)
    },
  }
}

export function createMockRecordTypeRepository(): RecordTypeRepository {
  const discussion = createMockConfigurationDiscussion('record_type')
  return {
    ...discussion.repository,
    async list(query) {
      await mockLatency(null)
      const rows = typeRows.map(row => ({
        ...row,
        updatedBy: row.updatedBy || person(0),
        commentCount: discussion.commentCount(row.id),
      }))
      return applyListQuery(rows as unknown as Record<string, unknown>[], query as any, ['name', 'code', 'description']) as unknown as Awaited<ReturnType<RecordTypeRepository['list']>>
    },
    async getById(id) {
      await mockLatency(null)
      const row = typeRows.find(item => item.id === id)
      if (!row) throw new Error('Record type not found')
      return structuredClone({ ...row, updatedBy: row.updatedBy || person(0) })
    },
    async getResolvedSchema(lookup) {
      await mockLatency(null)
      const recordType = lookup.id
        ? typeRows.find(item => item.id === lookup.id)
        : typeRows.find(item => item.code === lookup.code)
      if (!recordType) throw new Error('Record type not found')
      const assignedIds = new Set((recordType.attributes || []).map(item => item.attributeId))
      return structuredClone({
        recordType: { ...recordType, updatedBy: recordType.updatedBy || person(0) },
        attributes: attributeRows.filter(item => assignedIds.has(item.id) && item.status === 'active'),
        version: recordType.updatedAt,
      })
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
        createdBy: person(0),
        updatedBy: person(0),
      } as RecordType
      typeRows.unshift(row)
      discussion.track(row.id, 'created', `${person(0).name} created this record type`)
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
        updatedBy: person(0),
      }
      const nextStatus = input.status
      discussion.track(
        id,
        nextStatus === 'active' ? 'activated' : nextStatus === 'disabled' ? 'deactivated' : 'updated',
        nextStatus === 'active'
          ? `${person(0).name} activated this record type`
          : nextStatus === 'disabled'
            ? `${person(0).name} deactivated this record type`
            : `${person(0).name} updated this record type`,
      )
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
      discussion.clear(id)
      writeRows(RECORD_TYPE_KEY, typeRows)
      recalculateUsedByCounts()
      await mockLatency(null)
    },
    async removeMany(ids) {
      const idSet = new Set(ids)
      typeRows = typeRows.filter(item => !idSet.has(item.id))
      ids.forEach(id => discussion.clear(id))
      writeRows(RECORD_TYPE_KEY, typeRows)
      recalculateUsedByCounts()
      await mockLatency(null)
    },
  }
}

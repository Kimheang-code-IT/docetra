import type {
  DocumentTabSchema,
  FilterDef,
  TableColumnDef,
  WorkflowStage,
} from '~/types/docetra/common'
import type { AdapterKey } from '~/adapters'
import type { EntityAdapter } from '~/types/docetra/adapter'
import { adapters } from '~/adapters'
import { ApiEndpoints } from '~/utils/constants/api-endpoints'

export interface EntityConfig {
  key: AdapterKey
  routeBase: string
  titleKey: string
  descriptionKey?: string
  permission: string
  createPermission?: string
  icon: string
  groupKey: string
  views: Array<'table' | 'kanban' | 'hierarchy'>
  defaultView: 'table' | 'kanban' | 'hierarchy'
  readOnly?: boolean
  canCreate?: boolean
  /** Header/create-page label, e.g. docetra.config.createRecordAttribute → "New Attribute". */
  createLabelKey?: string
  canDelete?: boolean
  canComment?: boolean
  stages?: WorkflowStage[]
  columns: TableColumnDef[]
  filters: FilterDef[]
  titleField: string
  tabs: DocumentTabSchema[]
  statusOptions?: Array<{ label: string; value: string }>
}

const workflowStages: WorkflowStage[] = [
  { id: 'intake', code: 'intake', labelKey: 'docetra.stages.intake', order: 1, color: 'info' },
  { id: 'review', code: 'review', labelKey: 'docetra.stages.review', order: 2, color: 'warning' },
  { id: 'approval', code: 'approval', labelKey: 'docetra.stages.approval', order: 3, color: 'primary' },
  { id: 'completed', code: 'completed', labelKey: 'docetra.stages.completed', order: 4, color: 'success' },
]

/** Record module workflow (Incoming / Outgoing / Document / Master List). */
const recordWorkflowStages: WorkflowStage[] = [
  { id: 'created', code: 'created', labelKey: 'docetra.stages.created', order: 1, color: 'neutral' },
  { id: 'record_created', code: 'record_created', labelKey: 'docetra.stages.recordCreated', order: 2, color: 'info' },
  { id: 'observation_note', code: 'observation_note', labelKey: 'docetra.stages.observationNote', order: 3, color: 'warning' },
  { id: 'waiting_related_document', code: 'waiting_related_document', labelKey: 'docetra.stages.waitingRelatedDocument', order: 4, color: 'warning' },
  { id: 'submitted_director', code: 'submitted_director', labelKey: 'docetra.stages.submittedDirector', order: 5, color: 'primary' },
  { id: 'submitted_ddg', code: 'submitted_ddg', labelKey: 'docetra.stages.submittedDdg', order: 6, color: 'primary' },
  { id: 'submitted_dg', code: 'submitted_dg', labelKey: 'docetra.stages.submittedDg', order: 7, color: 'primary' },
  { id: 'further_measures', code: 'further_measures', labelKey: 'docetra.stages.furtherMeasures', order: 8, color: 'info' },
  { id: 'reply', code: 'reply', labelKey: 'docetra.stages.reply', order: 9, color: 'success' },
  { id: 'finished_final', code: 'finished_final', labelKey: 'docetra.stages.finishedFinal', order: 10, color: 'success' },
]

const statusFilter: FilterDef = {
  key: 'status',
  labelKey: 'docetra.fields.status',
  type: 'multiselect',
  options: [
    { label: 'Draft', value: 'draft', labelKey: 'docetra.status.draft' },
    { label: 'Active', value: 'active', labelKey: 'docetra.status.active' },
    { label: 'Pending', value: 'pending', labelKey: 'docetra.status.pending' },
    { label: 'Completed', value: 'completed', labelKey: 'docetra.status.completed' },
    { label: 'Archived', value: 'archived', labelKey: 'docetra.status.archived' },
  ],
}

const stageFilter: FilterDef = {
  key: 'stage',
  labelKey: 'docetra.fields.stage',
  type: 'multiselect',
  options: workflowStages.map(s => ({ label: s.code, value: s.code, labelKey: s.labelKey })),
}

const recordStageFilter: FilterDef = {
  key: 'stage',
  labelKey: 'docetra.fields.stage',
  type: 'multiselect',
  options: recordWorkflowStages.map(s => ({ label: s.code, value: s.code, labelKey: s.labelKey })),
}

const updatedAtDateFilter: FilterDef = {
  key: 'updatedAt',
  labelKey: 'docetra.fields.updatedAt',
  type: 'daterange',
}

const createdAtDateFilter: FilterDef = {
  key: 'createdAt',
  labelKey: 'docetra.fields.createdAt',
  type: 'daterange',
}

const occurredAtDateFilter: FilterDef = {
  key: 'occurredAt',
  labelKey: 'docetra.fields.occurredAt',
  type: 'daterange',
}

function recordTabs(extraFields: DocumentTabSchema['sections'][0]['fields'] = []): DocumentTabSchema[] {
  return [
    {
      id: 'details',
      labelKey: 'docetra.tabs.details',
      sections: [{
        id: 'main',
        titleKey: 'docetra.sections.main',
        fields: [
          { key: 'referenceNumber', labelKey: 'docetra.fields.referenceNumber', type: 'text', required: true },
          { key: 'title', labelKey: 'docetra.fields.title', type: 'text', required: true, colSpan: 2 },
          {
            key: 'recordTypeId',
            labelKey: 'docetra.fields.recordType',
            type: 'select',
            optionsEndpoint: `${ApiEndpoints.RECORD_TYPES}/options`,
          },
          { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
          { key: 'stage', labelKey: 'docetra.fields.stage', type: 'select', options: recordStageFilter.options },
          { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2 },
          ...extraFields,
        ],
      }],
    },
    {
      id: 'organizations',
      labelKey: 'docetra.tabs.organizations',
      sections: [{
        id: 'orgs',
        titleKey: 'docetra.sections.organizations',
        fields: [
          { key: 'senderOrganization.name', labelKey: 'docetra.fields.sender', type: 'text' },
          { key: 'recipientOrganization.name', labelKey: 'docetra.fields.recipient', type: 'text' },
          { key: 'ownerDepartment.name', labelKey: 'docetra.fields.ownerDepartment', type: 'text' },
        ],
      }],
    },
    {
      id: 'files',
      labelKey: 'docetra.tabs.files',
      sections: [{
        id: 'files',
        titleKey: 'docetra.sections.files',
        fields: [
          { key: 'attachmentCount', labelKey: 'docetra.fields.attachments', type: 'number', readOnly: true },
        ],
      }],
    },
  ]
}

function masterDataTabs(fields: DocumentTabSchema['sections'][0]['fields']): DocumentTabSchema[] {
  return [{
    id: 'details',
    labelKey: 'docetra.tabs.details',
    sections: [{
      id: 'main',
      titleKey: 'docetra.sections.main',
      fields,
    }],
  }]
}

export const entityConfigs: Record<string, EntityConfig> = {
  meetingTopics: {
    key: 'meetingTopics',
    routeBase: '/meetings/topics',
    titleKey: 'docetra.pages.meetingTopic',
    descriptionKey: 'docetra.descriptions.meetingTopic',
    permission: 'meetings.topics.view',
    icon: 'i-lucide-messages-square',
    groupKey: 'docetra.navigation.meeting',
    views: ['kanban', 'table'],
    defaultView: 'kanban',
    canCreate: true,
    createLabelKey: 'docetra.meetingBoard.createTopic',
    canComment: true,
    stages: workflowStages,
    titleField: 'title',
    columns: [
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'title', labelKey: 'docetra.fields.title', sortable: true, priority: 'high' },
      { key: 'recordTime', labelKey: 'docetra.fields.recordTime', sortable: true },
      { key: 'stage', labelKey: 'docetra.fields.stage', priority: 'high' },
      { key: 'tags', labelKey: 'docetra.fields.recordTag' },
      { key: 'childMeetingCount', labelKey: 'docetra.fields.childMeetings' },
    ],
    filters: [statusFilter, stageFilter],
    tabs: masterDataTabs([
      { key: 'title', labelKey: 'docetra.fields.title', type: 'text', required: true, colSpan: 2 },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', required: true, options: statusFilter.options },
      { key: 'stage', labelKey: 'docetra.fields.stage', type: 'select', required: true, options: stageFilter.options },
      { key: 'recordTime', labelKey: 'docetra.fields.recordTime', type: 'datetime', required: true },
      { key: 'tags', labelKey: 'docetra.fields.recordTag', type: 'csv-list', colSpan: 2 },
    ]),
  },

  meetingHistory: {
    key: 'meetingHistory',
    routeBase: '/meetings/history',
    titleKey: 'docetra.pages.meetingHistory',
    descriptionKey: 'docetra.descriptions.meetingHistory',
    permission: 'meetings.history.view',
    icon: 'i-lucide-history',
    groupKey: 'docetra.navigation.meeting',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    createLabelKey: 'docetra.meetingBoard.createMeeting',
    canComment: true,
    stages: workflowStages,
    titleField: 'title',
    columns: [
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'stage', labelKey: 'docetra.fields.stage', priority: 'high' },
      { key: 'letterNumber', labelKey: 'docetra.fields.letterNumber', sortable: true },
      { key: 'title', labelKey: 'docetra.fields.letterSubject', sortable: true, priority: 'high' },
      { key: 'letterDate', labelKey: 'docetra.fields.letterDate', sortable: true },
      { key: 'meetingDate', labelKey: 'docetra.fields.meetingDate', sortable: true },
      { key: 'location', labelKey: 'docetra.fields.location' },
      { key: 'participants', labelKey: 'docetra.fields.participants' },
      { key: 'internalUnits', labelKey: 'docetra.fields.internalUnits', priority: 'low' },
      { key: 'externalUnits', labelKey: 'docetra.fields.externalUnits', priority: 'low' },
      { key: 'tags', labelKey: 'docetra.fields.recordTag', priority: 'low' },
    ],
    filters: [
      statusFilter,
      stageFilter,
      { key: 'meetingDate', labelKey: 'docetra.fields.meetingDate', type: 'daterange' },
    ],
    tabs: masterDataTabs([
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', required: true, options: statusFilter.options },
      { key: 'stage', labelKey: 'docetra.fields.stage', type: 'select', required: true, options: stageFilter.options },
      { key: 'letterNumber', labelKey: 'docetra.fields.letterNumber', type: 'text', required: true },
      { key: 'title', labelKey: 'docetra.fields.letterSubject', type: 'text', required: true },
      { key: 'letterDate', labelKey: 'docetra.fields.letterDate', type: 'date', required: true },
      { key: 'meetingDate', labelKey: 'docetra.fields.meetingDateTime', type: 'datetime', required: true },
      { key: 'location', labelKey: 'docetra.fields.location', type: 'text' },
      { key: 'participants', labelKey: 'docetra.fields.participants', type: 'csv-list', colSpan: 2 },
      { key: 'internalUnits', labelKey: 'docetra.fields.internalUnits', type: 'csv-list' },
      { key: 'externalUnits', labelKey: 'docetra.fields.externalUnits', type: 'csv-list' },
      { key: 'tags', labelKey: 'docetra.fields.recordTag', type: 'csv-list', colSpan: 2 },
    ]),
  },

  incomingDocuments: {
    key: 'incomingDocuments',
    routeBase: '/records/incoming-documents',
    titleKey: 'docetra.pages.incomingDocument',
    descriptionKey: 'docetra.descriptions.incomingDocument',
    permission: 'records.incoming_documents.view',
    icon: 'i-lucide-inbox',
    groupKey: 'docetra.navigation.record',
    views: ['table', 'kanban'],
    defaultView: 'table',
    canCreate: true,
    canComment: true,
    stages: recordWorkflowStages,
    titleField: 'title',
    columns: [
      { key: 'referenceNumber', labelKey: 'docetra.fields.referenceNumber', sortable: true, priority: 'high' },
      { key: 'title', labelKey: 'docetra.fields.title', sortable: true, priority: 'high' },
      { key: 'senderOrganization.name', labelKey: 'docetra.fields.sender' },
      { key: 'receivedDate', labelKey: 'docetra.fields.receivedDate', sortable: true },
      { key: 'owner.name', labelKey: 'docetra.fields.owner' },
      { key: 'assignee.name', labelKey: 'docetra.fields.assignee' },
      { key: 'stage', labelKey: 'docetra.fields.stage', priority: 'high' },
      { key: 'waiting', labelKey: 'docetra.fields.waiting' },
      { key: 'attachmentCount', labelKey: 'docetra.fields.attachments', priority: 'low' },
    ],
    filters: [
      statusFilter,
      recordStageFilter,
      { key: 'receivedDate', labelKey: 'docetra.fields.receivedDate', type: 'daterange' },
      { key: 'waiting', labelKey: 'docetra.fields.waiting', type: 'boolean' },
    ],
    tabs: recordTabs([
      { key: 'receivedDate', labelKey: 'docetra.fields.receivedDate', type: 'date' },
      {
        key: 'waiting',
        labelKey: 'docetra.fields.waiting',
        type: 'boolean',
        hintKey: 'docetra.fieldHints.waiting',
      },
      {
        key: 'priorityScore',
        labelKey: 'docetra.fields.priorityScore',
        type: 'number',
        helpKey: 'docetra.fieldHints.priorityScore',
      },
    ]),
  },

  outgoingDocuments: {
    key: 'outgoingDocuments',
    routeBase: '/records/outgoing-documents',
    titleKey: 'docetra.pages.outgoingDocument',
    descriptionKey: 'docetra.descriptions.outgoingDocument',
    permission: 'records.outgoing_documents.view',
    icon: 'i-lucide-send',
    groupKey: 'docetra.navigation.record',
    views: ['table', 'kanban'],
    defaultView: 'table',
    canCreate: true,
    canComment: true,
    stages: recordWorkflowStages,
    titleField: 'title',
    columns: [
      { key: 'referenceNumber', labelKey: 'docetra.fields.referenceNumber', sortable: true, priority: 'high' },
      { key: 'title', labelKey: 'docetra.fields.title', sortable: true, priority: 'high' },
      { key: 'recipientOrganization.name', labelKey: 'docetra.fields.recipient' },
      { key: 'sentDate', labelKey: 'docetra.fields.sentDate', sortable: true },
      { key: 'stage', labelKey: 'docetra.fields.stage' },
      { key: 'status', labelKey: 'docetra.fields.status' },
    ],
    filters: [
      statusFilter,
      recordStageFilter,
      { key: 'sentDate', labelKey: 'docetra.fields.sentDate', type: 'daterange' },
    ],
    tabs: recordTabs([
      { key: 'sentDate', labelKey: 'docetra.fields.sentDate', type: 'date' },
    ]),
  },

  documents: {
    key: 'documents',
    routeBase: '/records/documents',
    titleKey: 'docetra.pages.document',
    descriptionKey: 'docetra.descriptions.document',
    permission: 'records.documents.view',
    icon: 'i-lucide-file-text',
    groupKey: 'docetra.navigation.record',
    views: ['table', 'kanban'],
    defaultView: 'table',
    canCreate: true,
    canComment: true,
    stages: recordWorkflowStages,
    titleField: 'title',
    columns: [
      { key: 'referenceNumber', labelKey: 'docetra.fields.referenceNumber', sortable: true, priority: 'high' },
      { key: 'title', labelKey: 'docetra.fields.title', sortable: true, priority: 'high' },
      { key: 'recordTypeName', labelKey: 'docetra.fields.recordType' },
      { key: 'stage', labelKey: 'docetra.fields.stage' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', sortable: true },
    ],
    filters: [
      statusFilter,
      recordStageFilter,
      { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', type: 'daterange' },
    ],
    tabs: recordTabs(),
  },

  masterListRequests: {
    key: 'masterListRequests',
    routeBase: '/records/master-list-requests',
    titleKey: 'docetra.pages.masterListRequest',
    descriptionKey: 'docetra.descriptions.masterListRequest',
    permission: 'records.master_list_requests.view',
    icon: 'i-lucide-list-checks',
    groupKey: 'docetra.navigation.record',
    views: ['table', 'kanban'],
    defaultView: 'table',
    canCreate: true,
    canComment: true,
    stages: recordWorkflowStages,
    titleField: 'title',
    columns: [
      { key: 'referenceNumber', labelKey: 'docetra.fields.referenceNumber', sortable: true },
      { key: 'title', labelKey: 'docetra.fields.title', sortable: true },
      { key: 'stage', labelKey: 'docetra.fields.stage' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'owner.name', labelKey: 'docetra.fields.owner' },
      { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt' },
    ],
    filters: [
      statusFilter,
      recordStageFilter,
      { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', type: 'daterange' },
    ],
    tabs: recordTabs(),
  },

  recordLogs: {
    key: 'recordLogs',
    routeBase: '/records/record-logs',
    titleKey: 'docetra.pages.recordLog',
    descriptionKey: 'docetra.descriptions.recordLog',
    permission: 'records.logs.view',
    icon: 'i-lucide-scroll-text',
    groupKey: 'docetra.navigation.record',
    views: ['table'],
    defaultView: 'table',
    readOnly: true,
    canCreate: false,
    canDelete: false,
    canComment: false,
    titleField: 'summary',
    columns: [
      { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', sortable: true, priority: 'high', cell: 'datetime' },
      { key: 'action', labelKey: 'docetra.fields.action', priority: 'high', cell: 'badge' },
      { key: 'entityType', labelKey: 'docetra.fields.recordType', priority: 'medium', cell: 'badge' },
      { key: 'entityTitle', labelKey: 'docetra.fields.entity', priority: 'high' },
      { key: 'actor.name', labelKey: 'docetra.fields.actor', priority: 'medium', cell: 'person' },
      { key: 'organization.name', labelKey: 'docetra.fields.organization', priority: 'low' },
      { key: 'severity', labelKey: 'docetra.fields.severity', priority: 'medium', cell: 'badge' },
      { key: 'summary', labelKey: 'docetra.fields.summary', priority: 'high' },
      { key: 'correlationId', labelKey: 'docetra.fields.correlationId', priority: 'low' },
    ],
    filters: [
      {
        key: 'action',
        labelKey: 'docetra.fields.action',
        type: 'select',
        options: [
          { label: 'Created', value: 'created', labelKey: 'docetra.logActions.created' },
          { label: 'Updated', value: 'updated', labelKey: 'docetra.logActions.updated' },
          { label: 'Stage changed', value: 'stage_changed', labelKey: 'docetra.logActions.stage_changed' },
          { label: 'Shared', value: 'shared', labelKey: 'docetra.logActions.shared' },
        ],
      },
      {
        key: 'entityType',
        labelKey: 'docetra.fields.recordType',
        type: 'select',
        options: [
          { label: 'Incoming', value: 'incoming_document', labelKey: 'docetra.entityTypes.incoming_document' },
          { label: 'Outgoing', value: 'outgoing_document', labelKey: 'docetra.entityTypes.outgoing_document' },
          { label: 'Document', value: 'document', labelKey: 'docetra.entityTypes.document' },
          { label: 'Master list', value: 'master_list_request', labelKey: 'docetra.entityTypes.master_list_request' },
        ],
      },
      {
        key: 'severity',
        labelKey: 'docetra.fields.severity',
        type: 'select',
        options: [
          { label: 'Info', value: 'info', labelKey: 'docetra.severity.info' },
          { label: 'Warn', value: 'warn', labelKey: 'docetra.severity.warn' },
          { label: 'Error', value: 'error', labelKey: 'docetra.severity.error' },
        ],
      },
    ],
    tabs: [
      {
        id: 'event',
        labelKey: 'docetra.tabs.event',
        sections: [{
          id: 'summary',
          titleKey: 'docetra.sections.eventSummary',
          fields: [
            { key: 'action', labelKey: 'docetra.fields.action', type: 'text', readOnly: true },
            { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', type: 'datetime', readOnly: true },
            { key: 'severity', labelKey: 'docetra.fields.severity', type: 'text', readOnly: true },
            { key: 'category', labelKey: 'docetra.fields.category', type: 'text', readOnly: true },
            { key: 'summary', labelKey: 'docetra.fields.summary', type: 'textarea', readOnly: true, colSpan: 2 },
            { key: 'changesSummary', labelKey: 'docetra.fields.changes', type: 'textarea', readOnly: true, colSpan: 2 },
          ],
        }],
      },
      {
        id: 'record',
        labelKey: 'docetra.tabs.linkedRecord',
        sections: [{
          id: 'linked',
          titleKey: 'docetra.sections.linkedRecord',
          fields: [
            { key: 'entityType', labelKey: 'docetra.fields.recordType', type: 'text', readOnly: true },
            { key: 'entityId', labelKey: 'docetra.fields.recordId', type: 'text', readOnly: true },
            { key: 'entityTitle', labelKey: 'docetra.fields.entity', type: 'text', readOnly: true, colSpan: 2 },
            { key: 'organization.name', labelKey: 'docetra.fields.organization', type: 'text', readOnly: true },
            { key: 'actor.name', labelKey: 'docetra.fields.actor', type: 'text', readOnly: true },
          ],
        }],
      },
      {
        id: 'context',
        labelKey: 'docetra.tabs.context',
        sections: [{
          id: 'request',
          titleKey: 'docetra.sections.requestContext',
          fields: [
            { key: 'correlationId', labelKey: 'docetra.fields.correlationId', type: 'text', readOnly: true },
            { key: 'category', labelKey: 'docetra.fields.category', type: 'text', readOnly: true },
            { key: 'createdAt', labelKey: 'docetra.fields.createdAt', type: 'datetime', readOnly: true },
          ],
        }],
      },
    ],
  },

  departments: {
    key: 'departments',
    routeBase: '/organizations/departments',
    titleKey: 'docetra.pages.department',
    descriptionKey: 'docetra.descriptions.department',
    permission: 'organizations.departments.view',
    icon: 'i-lucide-network',
    groupKey: 'docetra.navigation.organization',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: true,
    titleField: 'name',
    columns: [
      { key: 'code', labelKey: 'docetra.fields.code', sortable: true, priority: 'high' },
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true, priority: 'high' },
      { key: 'parentName', labelKey: 'docetra.fields.parent' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'officerCount', labelKey: 'docetra.fields.officerCount' },
      { key: 'relatedRecordCount', labelKey: 'docetra.fields.relatedRecords' },
      { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt', sortable: true },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'parentName', labelKey: 'docetra.fields.parent', type: 'text' },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
      { key: 'contactEmail', labelKey: 'docetra.fields.email', type: 'text' },
    ]),
  },

  companies: {
    key: 'companies',
    routeBase: '/organizations/companies',
    titleKey: 'docetra.pages.company',
    descriptionKey: 'docetra.descriptions.company',
    permission: 'organizations.companies.view',
    icon: 'i-lucide-building',
    groupKey: 'docetra.navigation.organization',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: true,
    titleField: 'name',
    columns: [
      { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'purposeName', labelKey: 'docetra.fields.purpose' },
      { key: 'sectorName', labelKey: 'docetra.fields.sector' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'relatedRecordCount', labelKey: 'docetra.fields.relatedRecords' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'purposeName', labelKey: 'docetra.fields.purpose', type: 'text' },
      { key: 'sectorName', labelKey: 'docetra.fields.sector', type: 'text' },
      { key: 'registrationNumber', labelKey: 'docetra.fields.registrationNumber', type: 'text' },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
    ]),
  },

  companyPurposes: {
    key: 'companyPurposes',
    routeBase: '/organizations/company-purposes',
    titleKey: 'docetra.pages.companyPurpose',
    descriptionKey: 'docetra.descriptions.companyPurpose',
    permission: 'organizations.company_purposes.view',
    icon: 'i-lucide-target',
    groupKey: 'docetra.navigation.organization',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: false,
    titleField: 'name',
    columns: [
      { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'usageCount', labelKey: 'docetra.fields.usage' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'updatedAt', labelKey: 'docetra.fields.updatedAt' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2 },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
    ]),
  },

  companySectors: {
    key: 'companySectors',
    routeBase: '/organizations/company-sectors',
    titleKey: 'docetra.pages.companySector',
    descriptionKey: 'docetra.descriptions.companySector',
    permission: 'organizations.company_sectors.view',
    icon: 'i-lucide-pie-chart',
    groupKey: 'docetra.navigation.organization',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: false,
    titleField: 'name',
    columns: [
      { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'usageCount', labelKey: 'docetra.fields.usage' },
      { key: 'status', labelKey: 'docetra.fields.status' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2 },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
    ]),
  },

  officers: {
    key: 'officers',
    routeBase: '/organizations/officers',
    titleKey: 'docetra.pages.officer',
    descriptionKey: 'docetra.descriptions.officer',
    permission: 'organizations.officers.view',
    icon: 'i-lucide-badge-check',
    groupKey: 'docetra.navigation.organization',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: true,
    titleField: 'name',
    columns: [
      { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'email', labelKey: 'docetra.fields.email' },
      { key: 'departmentName', labelKey: 'docetra.fields.department' },
      { key: 'titleRole', labelKey: 'docetra.fields.titleRole' },
      { key: 'status', labelKey: 'docetra.fields.status' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'email', labelKey: 'docetra.fields.email', type: 'text' },
      { key: 'phone', labelKey: 'docetra.fields.phone', type: 'text' },
      { key: 'departmentName', labelKey: 'docetra.fields.department', type: 'text' },
      { key: 'titleRole', labelKey: 'docetra.fields.titleRole', type: 'text' },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
    ]),
  },

  roles: {
    key: 'roles',
    routeBase: '/user-management/roles',
    titleKey: 'docetra.pages.role',
    descriptionKey: 'docetra.descriptions.role',
    permission: 'users.roles.view',
    icon: 'i-lucide-shield',
    groupKey: 'docetra.navigation.userManagement',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: false,
    titleField: 'name',
    columns: [
      { key: 'name', labelKey: 'docetra.fields.roleName', sortable: true, priority: 'high' },
      { key: 'userCount', labelKey: 'docetra.fields.users', sortable: true, priority: 'high' },
      { key: 'permissionCount', labelKey: 'docetra.fields.permissions', priority: 'high' },
      { key: 'status', labelKey: 'docetra.fields.status', priority: 'high' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: [
      {
        id: 'details',
        labelKey: 'docetra.tabs.details',
        sections: [
          {
            id: 'identity',
            titleKey: 'docetra.sections.main',
            fields: [
              { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
              { key: 'name', labelKey: 'docetra.fields.roleName', type: 'text', required: true },
              { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
              { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2 },
            ],
          },
          {
            id: 'permissions',
            titleKey: 'docetra.sections.permissions',
            fields: [
              {
                key: 'permissionRows',
                labelKey: 'docetra.fields.permissions',
                type: 'permission-matrix',
                colSpan: 2,
              },
            ],
          },
        ],
      },
    ],
  },

  users: {
    key: 'users',
    routeBase: '/user-management/users',
    titleKey: 'docetra.pages.user',
    descriptionKey: 'docetra.descriptions.user',
    permission: 'users.users.view',
    icon: 'i-lucide-user',
    groupKey: 'docetra.navigation.userManagement',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: false,
    titleField: 'name',
    columns: [
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'email', labelKey: 'docetra.fields.email', sortable: true },
      { key: 'roleName', labelKey: 'docetra.fields.role' },
      { key: 'officerName', labelKey: 'docetra.fields.officer' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'lastLoginAt', labelKey: 'docetra.fields.lastLogin' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'email', labelKey: 'docetra.fields.email', type: 'text', required: true },
      { key: 'roleName', labelKey: 'docetra.fields.role', type: 'text' },
      { key: 'officerName', labelKey: 'docetra.fields.officer', type: 'text' },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
    ]),
  },

  recordTypes: {
    key: 'recordTypes',
    routeBase: '/configuration/record-types',
    titleKey: 'docetra.pages.recordType',
    descriptionKey: 'docetra.descriptions.recordType',
    permission: 'configuration.record_types.view',
    icon: 'i-lucide-shapes',
    groupKey: 'docetra.navigation.configuration',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: false,
    titleField: 'name',
    columns: [
      { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'workflowEnabled', labelKey: 'docetra.fields.workflow' },
      { key: 'stageCount', labelKey: 'docetra.fields.stages' },
      { key: 'attributeCount', labelKey: 'docetra.fields.attributes' },
      { key: 'usageCount', labelKey: 'docetra.fields.usage' },
      { key: 'status', labelKey: 'docetra.fields.status' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'description', labelKey: 'docetra.fields.description', type: 'textarea', colSpan: 2 },
      { key: 'workflowEnabled', labelKey: 'docetra.fields.workflow', type: 'boolean' },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
    ]),
  },

  recordAttributes: {
    key: 'recordAttributes',
    routeBase: '/configuration/record-attributes',
    titleKey: 'docetra.pages.recordAttribute',
    descriptionKey: 'docetra.descriptions.recordAttribute',
    permission: 'configuration.record_attributes.view',
    icon: 'i-lucide-list-tree',
    groupKey: 'docetra.navigation.configuration',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: false,
    titleField: 'name',
    columns: [
      { key: 'code', labelKey: 'docetra.fields.code', sortable: true },
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'fieldType', labelKey: 'docetra.fields.fieldType' },
      { key: 'required', labelKey: 'docetra.fields.required' },
      { key: 'usageCount', labelKey: 'docetra.fields.usage' },
      { key: 'status', labelKey: 'docetra.fields.status' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'code', labelKey: 'docetra.fields.code', type: 'text', required: true },
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      {
        key: 'fieldType',
        labelKey: 'docetra.fields.fieldType',
        type: 'select',
        options: [
          { label: 'Short text', value: 'short_text', labelKey: 'docetra.config.dataType.short_text' },
          { label: 'Long text', value: 'long_text', labelKey: 'docetra.config.dataType.long_text' },
          { label: 'Rich text', value: 'rich_text', labelKey: 'docetra.config.dataType.rich_text' },
          { label: 'Integer', value: 'integer', labelKey: 'docetra.config.dataType.integer' },
          { label: 'Decimal', value: 'decimal', labelKey: 'docetra.config.dataType.decimal' },
          { label: 'Boolean', value: 'boolean', labelKey: 'docetra.config.dataType.boolean' },
          { label: 'Date', value: 'date', labelKey: 'docetra.config.dataType.date' },
          { label: 'Date time', value: 'datetime', labelKey: 'docetra.config.dataType.datetime' },
          { label: 'Select', value: 'select', labelKey: 'docetra.config.dataType.select' },
          { label: 'Email', value: 'email', labelKey: 'docetra.config.dataType.email' },
          { label: 'Phone', value: 'phone', labelKey: 'docetra.config.dataType.phone' },
          { label: 'URL', value: 'url', labelKey: 'docetra.config.dataType.url' },
          { label: 'File', value: 'file', labelKey: 'docetra.config.dataType.file' },
        ],
      },
      { key: 'required', labelKey: 'docetra.fields.required', type: 'boolean' },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
    ]),
  },

  fileUploads: {
    key: 'fileUploads',
    routeBase: '/portal/file-upload',
    titleKey: 'docetra.pages.fileUpload',
    descriptionKey: 'docetra.descriptions.fileUpload',
    permission: 'portal.file_upload.view',
    icon: 'i-lucide-upload',
    groupKey: 'docetra.navigation.portal',
    views: ['table'],
    defaultView: 'table',
    canCreate: false,
    canComment: false,
    titleField: 'fileName',
    columns: [
      { key: 'fileName', labelKey: 'docetra.fields.fileName', sortable: true, priority: 'high' },
      { key: 'mimeType', labelKey: 'docetra.fields.mimeType' },
      { key: 'sizeBytes', labelKey: 'docetra.fields.size' },
      { key: 'uploader.name', labelKey: 'docetra.fields.uploader' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'storageSource', labelKey: 'docetra.fields.storage' },
      { key: 'linkedRecordTitle', labelKey: 'docetra.fields.linkedRecord' },
      { key: 'createdAt', labelKey: 'docetra.fields.uploadedAt', sortable: true },
    ],
    filters: [statusFilter, createdAtDateFilter],
    tabs: masterDataTabs([
      { key: 'fileName', labelKey: 'docetra.fields.fileName', type: 'text', readOnly: true },
      { key: 'mimeType', labelKey: 'docetra.fields.mimeType', type: 'text', readOnly: true },
      { key: 'sizeBytes', labelKey: 'docetra.fields.size', type: 'number', readOnly: true },
      { key: 'storageSource', labelKey: 'docetra.fields.storage', type: 'text', readOnly: true },
      { key: 'linkedRecordTitle', labelKey: 'docetra.fields.linkedRecord', type: 'text', readOnly: true },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'text', readOnly: true },
    ]),
  },

  googleDriveSync: {
    key: 'googleDriveSync',
    routeBase: '/portal/google-drive-sync',
    titleKey: 'docetra.pages.googleDriveSync',
    descriptionKey: 'docetra.descriptions.googleDriveSync',
    permission: 'portal.google_drive_sync.view',
    icon: 'i-lucide-cloud',
    groupKey: 'docetra.navigation.portal',
    views: ['table'],
    defaultView: 'table',
    canCreate: true,
    canComment: false,
    titleField: 'name',
    columns: [
      { key: 'name', labelKey: 'docetra.fields.name', sortable: true },
      { key: 'folderName', labelKey: 'docetra.fields.folder' },
      { key: 'status', labelKey: 'docetra.fields.status' },
      { key: 'filesSynced', labelKey: 'docetra.fields.filesSynced' },
      { key: 'lastSyncAt', labelKey: 'docetra.fields.lastSync' },
    ],
    filters: [statusFilter, updatedAtDateFilter],
    tabs: masterDataTabs([
      { key: 'name', labelKey: 'docetra.fields.name', type: 'text', required: true },
      { key: 'folderName', labelKey: 'docetra.fields.folder', type: 'text' },
      { key: 'status', labelKey: 'docetra.fields.status', type: 'select', options: statusFilter.options },
      { key: 'filesSynced', labelKey: 'docetra.fields.filesSynced', type: 'number', readOnly: true },
      { key: 'errorMessage', labelKey: 'docetra.fields.error', type: 'textarea', readOnly: true, colSpan: 2 },
    ]),
  },

  portalLogs: {
    key: 'portalLogs',
    routeBase: '/portal/portal-logs',
    titleKey: 'docetra.pages.portalLog',
    descriptionKey: 'docetra.descriptions.portalLog',
    permission: 'portal.logs.view',
    icon: 'i-lucide-clipboard-list',
    groupKey: 'docetra.navigation.portal',
    views: ['table'],
    defaultView: 'table',
    readOnly: true,
    canCreate: false,
    canComment: false,
    titleField: 'summary',
    columns: [
      { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', sortable: true },
      { key: 'action', labelKey: 'docetra.fields.action' },
      { key: 'actor.name', labelKey: 'docetra.fields.actor' },
      { key: 'target', labelKey: 'docetra.fields.target' },
      { key: 'summary', labelKey: 'docetra.fields.summary' },
    ],
    filters: [occurredAtDateFilter],
    tabs: masterDataTabs([
      { key: 'action', labelKey: 'docetra.fields.action', type: 'text', readOnly: true },
      { key: 'summary', labelKey: 'docetra.fields.summary', type: 'textarea', readOnly: true, colSpan: 2 },
      { key: 'target', labelKey: 'docetra.fields.target', type: 'text', readOnly: true },
      { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', type: 'datetime', readOnly: true },
    ]),
  },

  systemLogs: {
    key: 'systemLogs',
    routeBase: '/system-monitor/system-logs',
    titleKey: 'docetra.pages.systemLog',
    descriptionKey: 'docetra.descriptions.systemLog',
    permission: 'system.logs.view',
    icon: 'i-lucide-activity',
    groupKey: 'docetra.navigation.systemMonitor',
    views: ['table'],
    defaultView: 'table',
    readOnly: true,
    canCreate: false,
    canComment: false,
    titleField: 'message',
    columns: [
      { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', sortable: true },
      { key: 'level', labelKey: 'docetra.fields.level' },
      { key: 'source', labelKey: 'docetra.fields.source' },
      { key: 'message', labelKey: 'docetra.fields.message' },
      { key: 'correlationId', labelKey: 'docetra.fields.correlationId', priority: 'low' },
    ],
    filters: [
      {
        key: 'level',
        labelKey: 'docetra.fields.level',
        type: 'select',
        options: [
          { label: 'Info', value: 'info' },
          { label: 'Warn', value: 'warn' },
          { label: 'Error', value: 'error' },
          { label: 'Debug', value: 'debug' },
        ],
      },
      occurredAtDateFilter,
    ],
    tabs: masterDataTabs([
      { key: 'level', labelKey: 'docetra.fields.level', type: 'text', readOnly: true },
      { key: 'source', labelKey: 'docetra.fields.source', type: 'text', readOnly: true },
      { key: 'message', labelKey: 'docetra.fields.message', type: 'textarea', readOnly: true, colSpan: 2 },
      { key: 'correlationId', labelKey: 'docetra.fields.correlationId', type: 'text', readOnly: true },
      { key: 'occurredAt', labelKey: 'docetra.fields.occurredAt', type: 'datetime', readOnly: true },
    ]),
  },
}

export function getEntityConfig(key: string): EntityConfig {
  const config = entityConfigs[key]
  if (!config) throw new Error(`Unknown entity config: ${key}`)
  return config
}

export function getEntityAdapter<T = any>(key: AdapterKey): EntityAdapter<T> {
  return adapters[key] as unknown as EntityAdapter<T>
}

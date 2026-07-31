export interface PersonSummary {
  id: string
  name: string
  email?: string
  avatarUrl?: string
}

export interface OrganizationSummary {
  id: string
  name: string
  code?: string
}

export interface ApiMeta {
  page: number
  limit: number
  total: number
  totalPages?: number
  cursor?: string | null
  nextCursor?: string | null
}

export interface ApiErrorItem {
  code: string
  message: string
  field?: string
}

export interface ApiResponse<T> {
  data: T
  meta?: ApiMeta
  errors?: ApiErrorItem[]
}

export interface ListQuery {
  q?: string
  page?: number
  limit?: number
  sort?: string
  view?: 'table' | 'kanban' | 'hierarchy'
  stage?: string
  status?: string
  startDate?: string
  endDate?: string
  [key: string]: string | number | boolean | undefined
}

export interface WorkflowStage {
  id: string
  code: string
  labelKey: string
  order: number
  color?: string
}

export interface EntityComment {
  id: string
  entityType: string
  entityId: string
  body: string
  author: PersonSummary
  createdAt: string
  editedAt?: string
}

export interface ActivityEvent {
  id: string
  entityType: string
  entityId: string
  action: string
  actor?: PersonSummary
  summary: string
  occurredAt: string
  correlationId?: string
  metadata?: Record<string, unknown>
}

export interface AttachmentMeta {
  id: string
  name: string
  mimeType: string
  sizeBytes: number
  url?: string
  uploadedBy?: PersonSummary
  uploadedAt: string
  storageSource?: 'local' | 'google_drive'
}

export type FieldType =
  | 'text'
  | 'textarea'
  | 'number'
  | 'date'
  | 'datetime'
  | 'select'
  | 'multiselect'
  | 'boolean'
  | 'organization'
  | 'officer'
  | 'relation'
  | 'file'
  | 'url'
  | 'permission-matrix'

export interface FieldOption {
  label: string
  value: string
  labelKey?: string
}

export interface DocumentFieldSchema {
  key: string
  labelKey: string
  type: FieldType
  required?: boolean
  readOnly?: boolean
  colSpan?: 1 | 2
  options?: FieldOption[]
  /** Help text shown below the input (ERPNext-style field description). */
  helpKey?: string
  /** Hint shown via info icon (especially useful for checkboxes). Falls back to helpKey. */
  hintKey?: string
  placeholderKey?: string
}

export interface DocumentSectionSchema {
  id: string
  titleKey: string
  descriptionKey?: string
  fields: DocumentFieldSchema[]
}

export interface DocumentTabSchema {
  id: string
  labelKey: string
  sections: DocumentSectionSchema[]
}

export interface TableColumnDef {
  key: string
  labelKey: string
  sortable?: boolean
  width?: string
  priority?: 'high' | 'medium' | 'low'
  /** How the cell should render. Defaults are inferred from the key when omitted. */
  cell?: 'text' | 'badge' | 'datetime' | 'person'
}

export interface FilterDef {
  key: string
  labelKey: string
  type: 'select' | 'multiselect' | 'boolean' | 'date' | 'daterange'
  options?: FieldOption[]
}

export type EntityStatus = 'draft' | 'active' | 'archived' | 'disabled' | 'pending' | 'completed' | 'failed'

export interface BaseEntity {
  id: string
  title?: string
  name?: string
  code?: string
  status: string
  stage?: string
  createdAt: string
  updatedAt: string
  createdBy?: PersonSummary
  updatedBy?: PersonSummary
  owner?: PersonSummary
  assignee?: PersonSummary
  organization?: OrganizationSummary
  tags?: string[]
  attachmentCount?: number
  commentCount?: number
}

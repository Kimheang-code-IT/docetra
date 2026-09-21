export type ExportScope = 'all_matching' | 'current_page' | 'selected'

export type ExportFormat = 'csv' | 'xlsx'

export interface ExportFieldOption {
  label: string
  value: string
}

export interface ExportRequest {
  startDate?: string
  endDate?: string
  scope: ExportScope
  fieldCodes: string[]
  format?: ExportFormat
  /** Field code → label, used to match Excel template headers. */
  fieldLabels?: Record<string, string>
}

export type ExportJobStatus = 'queued' | 'processing' | 'completed' | 'failed' | 'cancelled'

export interface ExportJob {
  id: string
  status: ExportJobStatus
  resource: string
  createdAt: string
  fileName?: string
  downloadUrl?: string
  expiresAt?: string
  error?: string
}

export interface CreateExportJobInput extends ExportRequest {
  resource: string
  query?: Record<string, unknown>
  selectedIds?: string[]
  format: ExportFormat
}

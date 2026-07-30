export type ImportBatchStatus = 'success' | 'failed' | 'partial'

/** API-ready import batch model (FastAPI response shape). */
export interface ImportBatch {
  id: number
  fileName: string
  fileType: string
  fileSize: number
  importedAtIso: string
  importedBy: string
  status: ImportBatchStatus
  totalRows: number
  validRows: number
  invalidRows: number
  duplicateRows: number
}

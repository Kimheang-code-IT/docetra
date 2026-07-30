export interface ImportValidationError {
  row: number
  column: string
  message: string
}

export interface ImportValidationSummary {
  totalRows: number
  validRows: number
  duplicateRows: number
  invalidRows: number
}

export type ImportPhase = 'select' | 'preview' | 'uploading' | 'success' | 'error'

export const IMPORT_ACCEPTED_EXTENSIONS = ['.xlsx', '.xls', '.csv'] as const

export function isAcceptedImportFile(file: File): boolean {
  const name = file.name.toLowerCase()
  return IMPORT_ACCEPTED_EXTENSIONS.some((ext) => name.endsWith(ext))
}

export function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

import type { ImportBatch } from '~/types/import-batch'

const STATUSES = ['success', 'failed', 'partial'] as const
const TYPES = ['CSV', 'JSON', 'XLSX', 'XML'] as const
const FILE_NAMES = ['revenue_data', 'entity_backup', 'transaction_log', 'daily_sync'] as const

export const initialData: ImportBatch[] = Array.from({ length: 30 }, (_, i) => {
  const id = i + 1
  const fileType = TYPES[i % TYPES.length]!
  const status = STATUSES[i % STATUSES.length]!
  const fileName = `${FILE_NAMES[i % FILE_NAMES.length]!}_${2026 - (i % 3)}.${fileType.toLowerCase()}`
  const totalRows = 80 + i * 12
  const duplicateRows = Math.round(totalRows * 0.06)
  const invalidRows = status === 'failed' ? Math.round(totalRows * 0.4) : Math.round(totalRows * 0.04)
  const validRows = Math.max(0, totalRows - duplicateRows - invalidRows)
  const day = String(22 - (i % 10)).padStart(2, '0')
  const hour = String(9 + (i % 9)).padStart(2, '0')

  return {
    id,
    fileName,
    fileType,
    fileSize: Math.round((1 + i * 0.5) * 1024 * 1024),
    importedAtIso: `2026-03-${day}T${hour}:15:00.000Z`,
    importedBy: i % 3 === 0 ? 'admin' : i % 3 === 1 ? 'finance.officer' : 'data.entry',
    status,
    totalRows,
    validRows,
    invalidRows,
    duplicateRows,
  }
})

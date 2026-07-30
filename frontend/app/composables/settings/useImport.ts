import { ref, computed, type Ref } from 'vue'
import { useTableQuery } from '~/composables/table/useTableQuery'
import { useToast } from '@nuxt/ui/composables'
import type { DropdownMenuItem } from '@nuxt/ui'
import type { ImportBatch } from '~/types/import-batch'
import { initialData } from '~/data/import-history'
import { formatDate } from '~/utils/format/date'
import { formatFileSize } from '~/types/import-dialog'

function toDateTime(iso: string) {
  const parsed = new Date(iso)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime()
}

function toDayStart(value: string) {
  const parsed = new Date(`${value}T00:00:00`)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime()
}

function toDayEnd(value: string) {
  const parsed = new Date(`${value}T23:59:59.999`)
  return Number.isNaN(parsed.getTime()) ? null : parsed.getTime()
}

async function animateUploadProgress(progress: Ref<number>) {
  const steps = [12, 28, 46, 63, 81, 94, 100]
  for (const step of steps) {
    await new Promise((r) => setTimeout(r, 180))
    progress.value = step
  }
}

export function useImportManagement() {
  const { t } = useI18n()
  const toast = useToast()
  const { globalFilter, pagination } = useTableQuery({ initialSorting: [{ id: 'id', desc: true }] })
  const { formattedRange } = useGlobalFilter()

  const imports = ref<ImportBatch[]>(initialData)
  const isUploading = ref(false)
  const uploadProgress = ref(0)
  const selectedTypes = ref<string[] | null>(null)
  const selectedFileNames = ref<string[] | null>(null)

  const typeItems = computed(() =>
    [...new Set(imports.value.map((record) => record.fileType))]
      .sort((a, b) => a.localeCompare(b))
      .map((type) => ({ label: type, value: type })),
  )

  const fileNameItems = computed(() =>
    [...new Set(imports.value.map((record) => record.fileName))]
      .sort((a, b) => a.localeCompare(b))
      .map((name) => ({ label: name, value: name })),
  )

  const reportColumns = computed(() => [
    { key: 'fileName', label: t('pages.import.columns.fileName'), width: 220, text: true },
    { key: 'fileType', label: t('pages.import.columns.type'), width: 100 },
    { key: 'fileSize', label: t('pages.import.columns.size'), width: 100 },
    { key: 'importedAtIso', label: t('pages.import.columns.importedAt'), width: 180 },
    { key: 'status', label: t('pages.import.columns.status'), width: 110 },
  ])

  const filteredImports = computed(() => {
    let rows = imports.value

    if (selectedTypes.value?.length) {
      rows = rows.filter((record) => selectedTypes.value!.includes(record.fileType))
    }

    if (selectedFileNames.value?.length) {
      rows = rows.filter((record) => selectedFileNames.value!.includes(record.fileName))
    }

    const startDate = formattedRange.value.start ? toDayStart(formattedRange.value.start) : null
    const endDate = formattedRange.value.end ? toDayEnd(formattedRange.value.end) : null

    if (startDate || endDate) {
      rows = rows.filter((record) => {
        const importedAt = toDateTime(record.importedAtIso)
        if (!importedAt) return false
        if (startDate && importedAt < startDate) return false
        if (endDate && importedAt > endDate) return false
        return true
      })
    }

    if (globalFilter.value?.trim()) {
      const query = globalFilter.value.trim().toLowerCase()
      rows = rows.filter((record) =>
        record.fileName.toLowerCase().includes(query)
        || record.fileType.toLowerCase().includes(query)
        || record.importedBy.toLowerCase().includes(query)
        || record.status.toLowerCase().includes(query)
        || formatDate(record.importedAtIso).toLowerCase().includes(query)
        || String(record.id).includes(query),
      )
    }

    return rows
  })

  const paginatedImports = computed(() => {
    const { pageIndex, pageSize } = pagination.value
    const start = pageIndex * pageSize
    return filteredImports.value.slice(start, start + pageSize)
  })

  function formatImportedAt(iso: string) {
    return formatDate(iso)
  }

  function formatRecordSize(bytes: number) {
    return formatFileSize(bytes)
  }

  function getDropdownActions(record: ImportBatch): DropdownMenuItem[][] {
    return [[
      {
        label: t('pages.import.actions.viewLogs'),
        icon: 'i-lucide-scroll-text',
        onSelect: () => toast.add({
          title: t('pages.import.toasts.viewingLogs'),
          description: t('pages.import.toasts.viewingLogsDesc', { file: record.fileName }),
        }),
      },
      {
        label: t('actions.delete'),
        icon: 'i-lucide-trash',
        color: 'error' as const,
        onSelect: () => {
          imports.value = imports.value.filter((i) => i.id !== record.id)
          toast.add({ title: t('pages.import.toasts.recordRemoved'), color: 'error' })
        },
      },
    ]]
  }

  async function handleFileUpload(files: FileList | null) {
    if (!files || files.length === 0) return

    isUploading.value = true
    uploadProgress.value = 0

    await animateUploadProgress(uploadProgress)

    const file = files[0]
    if (!file) {
      isUploading.value = false
      uploadProgress.value = 0
      return
    }

    const ext = file.name.split('.').pop()?.toUpperCase() || 'UNKNOWN'
    const totalRows = Math.max(20, Math.round(file.size / 500))
    const duplicateRows = Math.round(totalRows * 0.05)
    const invalidRows = Math.round(totalRows * 0.03)
    const validRows = Math.max(0, totalRows - duplicateRows - invalidRows)

    const newRecord: ImportBatch = {
      id: Math.max(...imports.value.map((i) => i.id), 0) + 1,
      fileName: file.name,
      fileType: ext,
      fileSize: file.size,
      importedAtIso: new Date().toISOString(),
      importedBy: 'current.user',
      status: invalidRows > 0 ? 'partial' : 'success',
      totalRows,
      validRows,
      invalidRows,
      duplicateRows,
    }

    imports.value.unshift(newRecord)
    isUploading.value = false
    uploadProgress.value = 0

    toast.add({
      title: t('pages.import.toasts.uploadSuccess'),
      description: t('pages.import.toasts.uploadSuccessDesc', { file: file.name }),
      color: 'success',
    })
  }

  return {
    imports,
    globalFilter,
    pagination,
    reportColumns,
    filteredImports,
    paginatedImports,
    isUploading,
    uploadProgress,
    selectedTypes,
    typeItems,
    selectedFileNames,
    fileNameItems,
    formatImportedAt,
    formatRecordSize,
    getDropdownActions,
    handleFileUpload,
  }
}

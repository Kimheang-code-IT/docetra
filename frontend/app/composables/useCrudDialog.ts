import { computed, ref } from 'vue'

export type CrudConfirmMode = 'save' | 'delete'

export type CrudConfirmConfig = {
  title: string
  description: string[]
  type: 'primary' | 'error'
  submitLabel: string
  icon: string
}

type TranslateFn = {
  (key: string): string
  (key: string, params: Record<string, unknown>): string
}

/**
 * Shared overlay state for create / update / delete flows.
 * Confirm loading prevents duplicate API submissions while a mutation is in flight.
 */
export function useCrudDialog<T extends { id?: number }>() {
  const selectedRecord = ref<T | null>(null)
  const pendingRecord = ref<T | null>(null)
  const confirmMode = ref<CrudConfirmMode>('save')
  const isFormOpen = ref(false)
  const isConfirmOpen = ref(false)
  const isConfirmLoading = ref(false)

  function openCreate() {
    selectedRecord.value = null
    pendingRecord.value = null
    confirmMode.value = 'save'
    isFormOpen.value = true
  }

  function openUpdate(record: T) {
    selectedRecord.value = { ...record }
    pendingRecord.value = null
    confirmMode.value = 'save'
    isFormOpen.value = true
  }

  function openDelete(record: T) {
    selectedRecord.value = record
    pendingRecord.value = null
    confirmMode.value = 'delete'
    isConfirmOpen.value = true
  }

  function openSaveConfirm(record: T) {
    pendingRecord.value = { ...record }
    confirmMode.value = 'save'
    isConfirmOpen.value = true
  }

  function resetDialog() {
    selectedRecord.value = null
    pendingRecord.value = null
    isFormOpen.value = false
    isConfirmOpen.value = false
    isConfirmLoading.value = false
  }

  /** Runs a confirm mutation once; ignores re-entry while loading. */
  async function runConfirmAction(action: () => Promise<void>) {
    if (isConfirmLoading.value) return
    isConfirmLoading.value = true
    try {
      await action()
    } finally {
      isConfirmLoading.value = false
    }
  }

  return {
    selectedRecord,
    pendingRecord,
    confirmMode,
    isFormOpen,
    isConfirmOpen,
    isConfirmLoading,
    openCreate,
    openUpdate,
    openDelete,
    openSaveConfirm,
    resetDialog,
    runConfirmAction,
  }
}

/** Shared delete / save confirm copy used by data-entry, reward, and settings CRUD. */
export function useCrudConfirmConfig<T extends { id?: number }>(options: {
  t: TranslateFn
  confirmMode: ReturnType<typeof useCrudDialog<T>>['confirmMode']
  selectedRecord: ReturnType<typeof useCrudDialog<T>>['selectedRecord']
  /** Defaults to record.id; pass name for user/role delete copy. */
  getRecordLabel?: (record: T) => string | number
  deleteIcon?: string
  saveIcon?: string
}) {
  return computed<CrudConfirmConfig>(() => {
    const {
      t,
      confirmMode,
      selectedRecord,
      getRecordLabel,
      deleteIcon = 'i-lucide-trash-2',
      saveIcon = 'i-lucide-check-circle',
    } = options

    if (confirmMode.value === 'delete') {
      const record = selectedRecord.value
      const label = record
        ? (getRecordLabel?.(record) ?? record.id ?? '-')
        : '-'
      return {
        title: t('components.deleteDataTitle'),
        description: [
          t('components.deleteDataLead', { id: label }),
          t('components.deleteDataPointPermanent'),
          t('components.deleteDataPointCheck'),
          t('components.deleteDataPointUndo'),
        ],
        type: 'error',
        submitLabel: t('actions.delete'),
        icon: deleteIcon,
      }
    }

    const isUpdate = Boolean(selectedRecord.value)
    return {
      title: isUpdate ? t('components.saveDataTitle') : t('components.addDataTitle'),
      description: isUpdate
        ? [
            t('components.saveDataLead'),
            t('components.saveDataPointReview'),
            t('components.saveDataPointUpdate'),
          ]
        : [
            t('components.addDataLead'),
            t('components.addDataPointRequired'),
            t('components.addDataPointReady'),
          ],
      type: 'primary',
      submitLabel: isUpdate ? t('actions.save') : t('actions.confirm'),
      icon: saveIcon,
    }
  })
}

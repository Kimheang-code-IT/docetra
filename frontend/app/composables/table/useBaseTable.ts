import { ref } from 'vue'
import type { ColumnPinningState, RowSelectionState, VisibilityState } from '@tanstack/vue-table'
import { useI18n } from '#imports'
import { useToast } from '@nuxt/ui/composables'

export interface BaseTableOptions {
  initialVisibility?: VisibilityState
  initialColumnPinning?: ColumnPinningState
}

/**
 * Page-local table UI state (selection, visibility, analytics drawer).
 * CRUD form/confirm overlays live in `useCrudDialog` — do not duplicate them here.
 */
export function useBaseTable(options: BaseTableOptions = {}) {
  const { t } = useI18n()
  const toast = useToast()

  const rowSelection = ref<RowSelectionState>({})
  const columnVisibility = ref<VisibilityState>(options.initialVisibility || {})
  const columnPinning = ref<ColumnPinningState>(
    options.initialColumnPinning ?? { left: [], right: [] },
  )

  const isAnalyticsOpen = ref(false)
  const isDetailOpen = ref(false)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  function resetUiState() {
    rowSelection.value = {}
  }

  function setLoading(value: boolean) {
    isLoading.value = value
  }

  function setError(message: string | null) {
    error.value = message
  }

  function clearError() {
    error.value = null
  }

  return {
    t,
    toast,
    rowSelection,
    columnVisibility,
    columnPinning,
    isAnalyticsOpen,
    isDetailOpen,
    isLoading,
    error,
    resetUiState,
    setLoading,
    setError,
    clearError,
  }
}

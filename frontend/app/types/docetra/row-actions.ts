export type RowActionKey = 'detail' | 'logs' | 'delete' | 'edit' | 'duplicate'

export interface RowActionItem {
  key: RowActionKey | string
  labelKey?: string
  label?: string
  icon?: string
  color?: 'error' | 'primary' | 'neutral' | 'success' | 'warning' | 'info' | 'secondary'
  disabled?: boolean
  /** Hide this action for a given row when returning true. */
  hidden?: (row: Record<string, unknown>) => boolean
}

export const DEFAULT_ROW_ACTIONS: RowActionItem[] = [
  {
    key: 'detail',
    labelKey: 'docetra.rowActions.detail',
    icon: 'i-lucide-eye',
  },
  {
    key: 'logs',
    labelKey: 'docetra.rowActions.logs',
    icon: 'i-lucide-scroll-text',
  },
  {
    key: 'delete',
    labelKey: 'docetra.rowActions.delete',
    icon: 'i-lucide-trash-2',
    color: 'error',
  },
]

import type { DropdownMenuItem } from '@nuxt/ui'
import type { Ref } from 'vue'

interface CrudDropdownOptions<T extends { id: number }> {
  t: (key: string) => string
  selectedEntry: Ref<T | null>
  confirmMode: Ref<'save' | 'delete'>
  isFormOpen: Ref<boolean>
  isConfirmOpen: Ref<boolean>
}

export function useCrudDropdownActions<T extends { id: number }>(options: CrudDropdownOptions<T>) {
  const getDropdownActions = (entry: T): DropdownMenuItem[][] => {
    return [[
      {
        label: options.t('actions.edit'),
        icon: 'i-lucide-edit',
        onSelect: () => {
          options.selectedEntry.value = { ...entry }
          options.isFormOpen.value = true
        }
      },
      {
        label: options.t('actions.delete'),
        icon: 'i-lucide-trash',
        color: 'error' as const,
        onSelect: () => {
          options.selectedEntry.value = entry
          options.confirmMode.value = 'delete'
          options.isConfirmOpen.value = true
        }
      }
    ]]
  }

  return { getDropdownActions }
}

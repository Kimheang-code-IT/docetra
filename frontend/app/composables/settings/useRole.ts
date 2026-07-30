import { ref, computed } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { TABLE_HEADERS } from '~/constants/report-table'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import { useCrudConfirmConfig, useCrudDialog } from '~/composables/useCrudDialog'
import type { SystemRole } from '~/types/system-role'
import type { FormField } from '~/types/form'
import { initialData } from '~/data/system-role'
import { slicePage } from '~/utils/table/paginate-rows'

const ROLE_FILTER_BASE_NAMES = [
  'SuperAdmin',
  'Finance Admin',
  'Officer',
  'Editor',
  'Viewer',
] as const

const ROLE_PAGE_ITEMS = [
  'dashboard',
  'data-entry',
  'kind-total-revenue',
  'reward',
  'royalty-land-fee',
  'dpme-total-revenue',
  'financial-obligation',
  'rev-public-service',
  'royalty-state-response',
  'history',
  'settings:user-management',
  'settings:role-management',
  'settings:exchange-rates',
  'settings:import',
] as const

const ROLE_PERMISSION_ITEMS = ['view', 'edit', 'update'] as const

function toSystemRole(data: Record<string, unknown>, existing?: SystemRole | null): SystemRole {
  const pageAccess = Array.isArray(data.pageAccess)
    ? data.pageAccess.map((item) => String(item).trim()).filter(Boolean)
    : []

  return {
    ...(existing ?? { id: 0 }),
    ...data,
    pageAccess,
  } as SystemRole
}

export function useSystemRoleManagement() {
  const { toFilterOptions } = useTranslatedFilterOptions()
  const {
    t,
    toast,
    rowSelection,
    columnVisibility,
  } = useBaseTable({})

  const {
    sorting,
    globalFilter,
    columnFilters,
    pagination,
  } = useTableQuery({
    initialSorting: [{ id: 'id', desc: false }],
    includeGlobalDateRange: false,
  })

  const {
    selectedRecord: selectedRole,
    pendingRecord: pendingRole,
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
  } = useCrudDialog<SystemRole>()

  const confirmConfig = useCrudConfirmConfig({
    t,
    confirmMode,
    selectedRecord: selectedRole,
    getRecordLabel: (role) => role.name,
    deleteIcon: 'i-lucide-shield-off',
    saveIcon: 'i-lucide-shield-plus',
  })

  const roles = ref<SystemRole[]>(initialData)

  const roleFilterItems = computed(() => toFilterOptions(ROLE_FILTER_BASE_NAMES))
  const selectedRoles = ref<string[] | null>(null)

  const filteredRoles = computed(() => {
    let rows = roles.value

    if (selectedRoles.value?.length) {
      rows = rows.filter((role) =>
        selectedRoles.value!.some((base) => role.name.startsWith(base)),
      )
    }

    if (globalFilter.value?.trim()) {
      const query = globalFilter.value.trim().toLowerCase()
      rows = rows.filter((role) =>
        role.name.toLowerCase().includes(query)
        || role.pageAccess.some((page) => page.toLowerCase().includes(query))
        || String(role.id).includes(query),
      )
    }

    return rows
  })

  const paginatedRoles = computed(() =>
    slicePage(
      filteredRoles.value,
      pagination.value.pageIndex,
      pagination.value.pageSize,
      true,
    ),
  )

  const reportColumns = computed(() => [
    { key: 'id', label: TABLE_HEADERS.rank, width: 56 },
    { key: 'name', label: TABLE_HEADERS.name, width: 180, text: true },
    { key: 'pageAccess', label: TABLE_HEADERS.pageAccess, width: 480, text: true },
  ])

  const roleFormFields = computed<FormField[]>(() => [
    {
      key: 'name',
      label: t('pages.roleManagement.columns.name'),
      type: 'input',
      icon: 'i-lucide-shield',
      required: true,
    },
    {
      key: 'pageAccess',
      label: t('pages.roleManagement.columns.pageAccess'),
      type: 'permission-tree',
      items: [...ROLE_PAGE_ITEMS],
      childItems: [...ROLE_PERMISSION_ITEMS],
      required: true,
    },
  ])

  function getDropdownActions(role: SystemRole): DropdownMenuItem[][] {
    return [[
      {
        label: t('actions.edit'),
        icon: 'i-lucide-edit',
        onSelect: () => openUpdate({ ...role, pageAccess: [...role.pageAccess] }),
      },
      {
        label: t('actions.delete'),
        icon: 'i-lucide-trash',
        color: 'error' as const,
        onSelect: () => openDelete(role),
      },
    ]]
  }

  function handleSaveRequest(data: Record<string, unknown> | SystemRole) {
    openSaveConfirm(toSystemRole(data as Record<string, unknown>, selectedRole.value))
  }

  async function finalizeAction() {
    if (confirmMode.value === 'delete' && selectedRole.value) {
      const removed = selectedRole.value
      roles.value = roles.value.filter((role) => role.id !== removed.id)
      toast.add({
        title: t('pages.roleManagement.toasts.deleted'),
        description: t('pages.roleManagement.toasts.deletedDesc', { name: removed.name }),
        color: 'error',
      })
      resetDialog()
      return
    }

    if (confirmMode.value !== 'save' || !pendingRole.value) return

    const payload = pendingRole.value
    const isCreate = !payload.id || payload.id === 0

    if (isCreate) {
      const newId = Math.max(...roles.value.map((role) => role.id), 0) + 1
      roles.value.push({ ...payload, id: newId })
      toast.add({
        title: t('pages.roleManagement.toasts.added'),
        description: t('pages.roleManagement.toasts.addedDesc'),
        color: 'primary',
      })
    } else {
      const index = roles.value.findIndex((role) => role.id === payload.id)
      if (index !== -1) {
        roles.value[index] = payload
      }
      toast.add({
        title: t('pages.roleManagement.toasts.updated'),
        description: t('pages.roleManagement.toasts.updatedDesc'),
        color: 'primary',
      })
    }

    resetDialog()
  }

  async function confirmAction() {
    await runConfirmAction(finalizeAction)
  }

  return {
    rowSelection,
    sorting,
    globalFilter,
    columnVisibility,
    columnFilters,
    pagination,
    isFormOpen,
    isConfirmOpen,
    isConfirmLoading,
    selectedRole,
    roles,
    roleFilterItems,
    selectedRoles,
    totalRows: computed(() => roles.value.length),
    filteredRoles,
    paginatedRoles,
    reportColumns,
    confirmConfig,
    roleFormFields,
    getDropdownActions,
    handleSaveRequest,
    confirmAction,
    handleAddNew: openCreate,
  }
}

import { ref, computed } from 'vue'
import type { DropdownMenuItem } from '@nuxt/ui'
import { TABLE_HEADERS } from '~/constants/report-table'
import { useBaseTable } from '~/composables/table/useBaseTable'
import { useTableQuery } from '~/composables/table/useTableQuery'
import { useCrudConfirmConfig, useCrudDialog } from '~/composables/useCrudDialog'
import type { SystemUser } from '~/types/system-user'
import type { FormField } from '~/types/form'
import { initialData } from '~/data/system-user'
import { slicePage } from '~/utils/table/paginate-rows'

export const USER_ROLE_VALUES = ['SuperAdmin', 'Editor', 'Officer', 'Viewer'] as const

export type UserRoleValue = (typeof USER_ROLE_VALUES)[number]

const USER_ROLE_BADGE_COLOR: Record<UserRoleValue, 'primary' | 'secondary' | 'neutral'> = {
  SuperAdmin: 'primary',
  Editor: 'secondary',
  Officer: 'neutral',
  Viewer: 'neutral',
}

export function getUserRoleBadgeColor(role: string): 'primary' | 'secondary' | 'neutral' {
  if (role in USER_ROLE_BADGE_COLOR) {
    return USER_ROLE_BADGE_COLOR[role as UserRoleValue]
  }
  return 'neutral'
}

function toSystemUser(data: Record<string, unknown>, existing?: SystemUser | null): SystemUser {
  return {
    ...(existing ?? {
      id: 0,
      lastLogin: new Date().toISOString().slice(0, 10),
    }),
    ...data,
  } as SystemUser
}

export function useSystemUserManagement() {
  const { toFilterOptions } = useTranslatedFilterOptions()
  const {
    t,
    toast,
    rowSelection,
    columnVisibility,
  } = useBaseTable({
    initialVisibility: { password: false },
  })

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
    selectedRecord: selectedUser,
    pendingRecord: pendingUser,
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
  } = useCrudDialog<SystemUser>()

  const confirmConfig = useCrudConfirmConfig({
    t,
    confirmMode,
    selectedRecord: selectedUser,
    getRecordLabel: (user) => user.name,
    deleteIcon: 'i-lucide-user-minus',
    saveIcon: 'i-lucide-user-plus',
  })

  const users = ref<SystemUser[]>(initialData)
  const roleItems = computed(() => toFilterOptions(USER_ROLE_VALUES))
  const selectedRoles = ref<string[] | null>(null)

  const filteredUsers = computed(() => {
    let rows = users.value

    if (selectedRoles.value?.length) {
      rows = rows.filter((user) => selectedRoles.value!.includes(user.role))
    }

    if (globalFilter.value?.trim()) {
      const query = globalFilter.value.trim().toLowerCase()
      rows = rows.filter((user) =>
        user.name.toLowerCase().includes(query)
        || user.email.toLowerCase().includes(query)
        || user.role.toLowerCase().includes(query)
        || String(user.id).includes(query),
      )
    }

    return rows
  })

  const paginatedUsers = computed(() =>
    slicePage(
      filteredUsers.value,
      pagination.value.pageIndex,
      pagination.value.pageSize,
      true,
    ),
  )

  const reportColumns = computed(() => [
    { key: 'id', label: TABLE_HEADERS.rank, width: 56 },
    { key: 'name', label: TABLE_HEADERS.name, width: 160, text: true },
    { key: 'role', label: TABLE_HEADERS.role, width: 120 },
    { key: 'email', label: TABLE_HEADERS.email, width: 200, text: true },
    { key: 'lastLogin', label: TABLE_HEADERS.lastLogin, width: 160 },
  ])

  const userFormFields = computed<FormField[]>(() => [
    {
      key: 'name',
      label: t('pages.userManagement.columns.name'),
      type: 'input',
      icon: 'i-lucide-user',
      required: true,
    },
    {
      key: 'role',
      label: t('pages.userManagement.columns.role'),
      type: 'select',
      items: toFilterOptions(USER_ROLE_VALUES),
      icon: 'i-lucide-shield-half',
      required: true,
    },
    {
      key: 'email',
      label: t('pages.userManagement.columns.email'),
      type: 'input',
      icon: 'i-lucide-mail',
      required: true,
    },
    {
      key: 'password',
      label: t('pages.userManagement.columns.password'),
      type: 'input',
      icon: 'i-lucide-lock',
      placeholder: 'Min 8 chars...',
    },
  ])

  function getDropdownActions(user: SystemUser): DropdownMenuItem[][] {
    return [
      [
        {
          label: t('actions.edit'),
          icon: 'i-lucide-user-cog',
          onSelect: () => openUpdate(user),
        },
        {
          label: t('actions.delete'),
          icon: 'i-lucide-user-x',
          color: 'error' as const,
          onSelect: () => openDelete(user),
        },
      ],
    ]
  }

  function handleSaveRequest(data: Record<string, unknown>) {
    openSaveConfirm(toSystemUser(data, selectedUser.value))
  }

  async function finalizeAction() {
    if (confirmMode.value === 'delete' && selectedUser.value) {
      const removed = selectedUser.value
      users.value = users.value.filter((user) => user.id !== removed.id)
      toast.add({
        title: t('pages.userManagement.toasts.deleted'),
        description: t('pages.userManagement.toasts.deletedDesc', { name: removed.name }),
        color: 'error',
      })
      resetDialog()
      return
    }

    if (confirmMode.value !== 'save' || !pendingUser.value) return

    const payload = pendingUser.value
    const isCreate = !payload.id || payload.id === 0

    if (isCreate) {
      const newId = Math.max(...users.value.map((user) => user.id), 0) + 1
      users.value.push({ ...payload, id: newId })
      toast.add({
        title: t('pages.userManagement.toasts.added'),
        description: t('pages.userManagement.toasts.addedDesc'),
        color: 'primary',
      })
    } else {
      const index = users.value.findIndex((user) => user.id === payload.id)
      if (index !== -1) {
        users.value[index] = payload
        toast.add({
          title: t('pages.userManagement.toasts.updated'),
          description: t('pages.userManagement.toasts.updatedDesc'),
          color: 'primary',
        })
      }
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
    selectedUser,
    users,
    roleItems,
    selectedRoles,
    filteredUsers,
    paginatedUsers,
    reportColumns,
    confirmConfig,
    userFormFields,
    getDropdownActions,
    handleSaveRequest,
    confirmAction,
    handleAddNew: openCreate,
  }
}

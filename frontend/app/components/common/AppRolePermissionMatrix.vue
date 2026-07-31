<script setup lang="ts">
import type { AppRolePermissionRow } from '~/types/docetra/entities'
import {
  ROLE_DOCUMENT_TYPES,
  ROLE_PERMISSION_ACTIONS,
  createEmptyPermissionRow,
} from '~/utils/role/permissions'

const rows = defineModel<AppRolePermissionRow[]>({ default: () => [] })

const props = withDefaults(
  defineProps<{
    disabled?: boolean
  }>(),
  {
    disabled: false,
  },
)

const { t, te } = useI18n()

/** Always list every document type; merge saved permission state. */
const displayRows = computed(() => {
  const byType = new Map(rows.value.map(row => [row.documentType, row]))
  return ROLE_DOCUMENT_TYPES.map((doc) => {
    const existing = byType.get(doc.value)
    if (existing) return existing
    return {
      ...createEmptyPermissionRow(doc.value),
      actions: [],
    }
  })
})

const actionColumns = computed(() => {
  const actions = [...ROLE_PERMISSION_ACTIONS]
  const cols: string[][] = [[], [], []]
  actions.forEach((action, i) => {
    cols[i % 3]!.push(action)
  })
  return cols
})

function ensureAllRows() {
  const byType = new Map(rows.value.map(row => [row.documentType, row]))
  const next = ROLE_DOCUMENT_TYPES.map((doc) => {
    const existing = byType.get(doc.value)
    if (existing) return existing
    return {
      ...createEmptyPermissionRow(doc.value),
      actions: [],
    }
  })
  const same
    = next.length === rows.value.length
      && next.every((row, i) => row.documentType === rows.value[i]?.documentType && row.id === rows.value[i]?.id)
  if (!same) rows.value = next
}

onMounted(ensureAllRows)
watch(rows, ensureAllRows, { deep: false })

function documentTypeLabel(value: string) {
  const found = ROLE_DOCUMENT_TYPES.find(d => d.value === value)
  if (found && te(found.labelKey)) return t(found.labelKey)
  return value.replaceAll('_', ' ')
}

function actionLabel(action: string) {
  const key = `docetra.rolePermissions.actions.${action}`
  return te(key) ? t(key) : action
}

function hasAction(row: AppRolePermissionRow, action: string) {
  return row.actions.includes(action)
}

function toggleAction(documentType: string, action: string, checked: boolean | 'indeterminate') {
  if (props.disabled) return
  ensureAllRows()
  rows.value = rows.value.map((row) => {
    if (row.documentType !== documentType) return row
    const set = new Set(row.actions)
    if (checked === true) set.add(action)
    else set.delete(action)
    return { ...row, actions: [...set] }
  })
}
</script>

<template>
  <div class="overflow-x-auto rounded-xl border border-default">
    <table class="min-w-full text-sm">
      <thead>
        <tr class="bg-elevated/80 text-left text-highlighted">
          <th class="whitespace-nowrap rounded-tl-xl px-4 py-3 font-semibold">
            {{ $t('docetra.rolePermissions.documentType') }}
          </th>
          <th class="min-w-80 rounded-tr-xl px-4 py-3 font-semibold">
            {{ $t('docetra.fields.permissions') }}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="row in displayRows"
          :key="row.documentType"
          class="align-top border-t border-default"
        >
          <td class="px-4 py-4 font-medium text-highlighted">
            {{ documentTypeLabel(row.documentType) }}
          </td>
          <td class="px-4 py-4">
            <div class="grid grid-cols-1 gap-x-6 gap-y-2 sm:grid-cols-3">
              <div
                v-for="(col, colIndex) in actionColumns"
                :key="colIndex"
                class="space-y-2"
              >
                <label
                  v-for="action in col"
                  :key="action"
                  class="flex cursor-pointer items-center gap-2 text-sm text-highlighted"
                >
                  <UCheckbox
                    :model-value="hasAction(row, action)"
                    :disabled="disabled"
                    @update:model-value="(v) => toggleAction(row.documentType, action, v)"
                  />
                  <span>{{ actionLabel(action) }}</span>
                </label>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

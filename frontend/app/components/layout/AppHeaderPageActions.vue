<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type { ExportFieldOption, ExportRequest } from '~/types/docetra/export'
import { useAppHeader } from '~/composables/layout/useAppHeader'

/**
 * Registers reusable header actions (refresh / more / optional create).
 * Create is opt-in: pass :can-create="true" only on pages that open a /new flow.
 * Use createButtons for multiple create actions (e.g. Add Topic + Add Meeting).
 */
const props = withDefaults(defineProps<{
  canCreate?: boolean
  createLabel?: string
  createIcon?: string
  createButtons?: Array<{ label: string, icon?: string }>
  refreshing?: boolean
  moreItems?: DropdownMenuItem[][]
  exportFields?: ExportFieldOption[]
  selectedCount?: number
  exporting?: boolean
}>(), {
  canCreate: false,
  createIcon: 'i-lucide-plus',
  refreshing: false,
  moreItems: undefined,
  exportFields: () => [],
  selectedCount: 0,
  exporting: false,
})

const emit = defineEmits<{
  refresh: []
  create: []
  createButton: [index: number]
  export: [request: ExportRequest]
}>()

const { t } = useI18n()
const toast = useToast()
const { setActions, clearActions } = useAppHeader()
const slots = useSlots()
const ownerId = ref(0)
const exportOpen = ref(false)
/** Keep-alive pages stay mounted; only the active one may teleport into the header. */
const headerTeleportActive = ref(true)

const resolvedCreateLabel = computed(() =>
  props.createLabel || t('docetra.actions.addItem'),
)

const defaultMoreItems = computed<DropdownMenuItem[][]>(() => [[
  {
    label: t('actions.export'),
    icon: 'i-lucide-download',
    onSelect: () => { exportOpen.value = true },
  },
]])

function withoutPrint(items: DropdownMenuItem[][]): DropdownMenuItem[][] {
  const printLabels = new Set([
    'print',
    t('docetra.document.print').trim().toLowerCase(),
    t('docetra.rolePermissions.actions.print').trim().toLowerCase(),
  ])
  return items
    .map(group => group.filter((item: any) =>
      !String(item.icon || '').includes('printer')
      && !printLabels.has(String(item.label || '').trim().toLowerCase()),
    ))
    .filter(group => group.length > 0)
}

const menuItems = computed(() => {
  const custom = props.moreItems || []
  const exportItem = defaultMoreItems.value[0] || []
  return withoutPrint([
    [...exportItem, ...(custom[0] || [])],
    ...custom.slice(1),
  ])
})

function submitExport(request: ExportRequest) {
  emit('export', request)
  if (!props.exporting) {
    exportOpen.value = false
    toast.add({ title: t('docetra.exportDialog.requestReady'), color: 'success' })
  }
}

function syncActions() {
  const createButtons = props.createButtons?.length
    ? props.createButtons.map((button, index) => ({
        label: button.label,
        icon: button.icon || 'i-lucide-plus',
        onClick: () => emit('createButton', index),
      }))
    : undefined

  ownerId.value = setActions({
    canCreate: props.canCreate === true || Boolean(createButtons?.length),
    createLabel: resolvedCreateLabel.value,
    createIcon: props.createIcon || 'i-lucide-plus',
    createButtons,
    refreshing: Boolean(props.refreshing),
    moreItems: menuItems.value,
    onCreate: () => emit('create'),
    onRefresh: () => emit('refresh'),
  })
}

watch(
  () => [
    props.canCreate,
    resolvedCreateLabel.value,
    props.createIcon,
    props.createButtons,
    props.refreshing,
    menuItems.value,
  ] as const,
  () => syncActions(),
  { immediate: true, deep: true },
)

// Re-register after keep-alive / back-navigation races with the previous page’s clear.
onActivated(() => {
  headerTeleportActive.value = true
  syncActions()
})

onDeactivated(() => {
  headerTeleportActive.value = false
  clearActions(ownerId.value)
})

onBeforeUnmount(() => {
  headerTeleportActive.value = false
  clearActions(ownerId.value)
})
</script>

<template>
  <Teleport v-if="headerTeleportActive && slots.leading" defer to="#app-header-leading">
    <div class="contents">
      <slot name="leading" />
    </div>
  </Teleport>

  <Teleport v-if="headerTeleportActive && slots.default" defer to="#app-header-trailing">
    <div class="contents">
      <slot />
    </div>
  </Teleport>

  <CommonAppExportDialog
    v-model:open="exportOpen"
    :fields="props.exportFields"
    :selected-count="props.selectedCount"
    :loading="props.exporting"
    @submit="submitExport"
  />
</template>

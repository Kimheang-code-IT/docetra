<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
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
}>(), {
  canCreate: false,
  createIcon: 'i-lucide-plus',
  refreshing: false,
  moreItems: undefined,
})

const emit = defineEmits<{
  refresh: []
  create: []
  createButton: [index: number]
}>()

const { t } = useI18n()
const toast = useToast()
const { setActions, clearActions } = useAppHeader()
const slots = useSlots()
const ownerId = ref(0)

const resolvedCreateLabel = computed(() =>
  props.createLabel || t('docetra.actions.addItem'),
)

const defaultMoreItems = computed<DropdownMenuItem[][]>(() => [[
  {
    label: t('actions.export'),
    icon: 'i-lucide-download',
    onSelect: () => toast.add({ title: t('docetra.document.comingSoon'), color: 'neutral' }),
  },
  {
    label: t('docetra.document.print'),
    icon: 'i-lucide-printer',
    onSelect: () => toast.add({ title: t('docetra.document.comingSoon'), color: 'neutral' }),
  },
]])

const menuItems = computed(() => props.moreItems?.length ? props.moreItems : defaultMoreItems.value)

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
  syncActions()
})

onBeforeUnmount(() => {
  clearActions(ownerId.value)
})
</script>

<template>
  <Teleport v-if="slots.leading" defer to="#app-header-leading">
    <div class="contents">
      <slot name="leading" />
    </div>
  </Teleport>

  <Teleport v-if="slots.default" defer to="#app-header-trailing">
    <div class="contents">
      <slot />
    </div>
  </Teleport>
</template>

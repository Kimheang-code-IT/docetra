<script setup lang="ts">
import { useAppHeader } from '~/composables/layout/useAppHeader'

/**
 * List/workspace shell. Pass :can-create="true" (and optional createLabelKey)
 * only when the page has a create/new flow.
 * Use createButtons for multiple header create actions.
 */
const props = withDefaults(defineProps<{
  titleKey: string
  descriptionKey?: string
  icon?: string
  canCreate?: boolean
  createLabelKey?: string
  createButtons?: Array<{ labelKey: string, icon?: string }>
}>(), {
  canCreate: false,
})

const emit = defineEmits<{
  create: []
  createButton: [index: number]
  refresh: []
}>()

const { t } = useI18n()
const { setTitle, setBreadcrumbs, setBadges } = useAppHeader()

const resolvedCreateButtons = computed(() =>
  (props.createButtons || []).map(button => ({
    label: t(button.labelKey),
    icon: button.icon,
  })),
)

const resolvedCreateLabel = computed(() => {
  if (props.createLabelKey) return t(props.createLabelKey)
  // Match Record Attribute style: "New {Page}" instead of generic "Add Item".
  return t('docetra.document.new', { entity: t(props.titleKey) })
})

watch(
  () => [props.titleKey, t(props.titleKey)] as const,
  ([, label]) => setTitle(label),
  { immediate: true },
)

onBeforeUnmount(() => {
  setTitle('')
  setBreadcrumbs([])
  setBadges([])
})

useHead(() => ({
  title: `${t(props.titleKey)} · ${t('docetra.brand.name')}`,
}))
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden bg-muted/20">
    <LayoutAppHeaderPageActions
      :can-create="props.canCreate === true && !resolvedCreateButtons.length"
      :create-label="resolvedCreateLabel"
      :create-buttons="resolvedCreateButtons.length ? resolvedCreateButtons : undefined"
      @refresh="emit('refresh')"
      @create="emit('create')"
      @create-button="emit('createButton', $event)"
    />

    <div class="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden px-1.5 pt-1.5 pb-0">
      <slot />
    </div>
  </div>
</template>

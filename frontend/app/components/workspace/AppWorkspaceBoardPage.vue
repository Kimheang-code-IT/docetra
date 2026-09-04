<script setup lang="ts">
import { useMediaQuery } from '@vueuse/core'
import type { BoardViewMode } from '~/composables/common/useBoardViewMode'

/**
 * Shared workspace board page for meeting topic / record stage / record log.
 * Owns page chrome + two-pane board shell; domain boards only fill rail/content slots.
 */
const collapsed = defineModel<boolean>('collapsed', { default: false })
const railSearch = defineModel<string>('railSearch')
const headerSearch = defineModel<string>('headerSearch')
const dateStart = defineModel<string>('dateStart')
const dateEnd = defineModel<string>('dateEnd')
const viewMode = defineModel<BoardViewMode | undefined>('viewMode')

const props = withDefaults(defineProps<{
  titleKey: string
  descriptionKey?: string
  icon?: string
  canCreate?: boolean
  createButtons?: Array<{ labelKey: string, icon?: string }>
  railTitleKey: string
  railIcon: string
  expandLabelKey: string
  collapseLabelKey: string
  railSearchPlaceholderKey?: string
  headerSearchPlaceholderKey?: string
  pending?: boolean
  showPendingOverlay?: boolean
  error?: string | null
}>(), {
  canCreate: false,
  pending: false,
  showPendingOverlay: false,
})

const emit = defineEmits<{
  create: []
  createButton: [index: number]
  refresh: []
  retry: []
}>()

const mobileOpen = ref(false)
const isSmallScreen = useMediaQuery('(max-width: 1023px)')

/** Desktop icon-rail state; small screens always show the full rail. */
const railCollapsed = computed(() =>
  isSmallScreen.value ? false : collapsed.value,
)

function closeMobile() {
  mobileOpen.value = false
}

function onRailSelect(handler?: () => void) {
  handler?.()
  if (isSmallScreen.value) closeMobile()
}

defineExpose({
  railCollapsed,
  isSmallScreen,
  closeMobile,
  onRailSelect,
})
</script>

<template>
  <WorkspaceAppWorkspacePage
    :title-key="titleKey"
    :description-key="descriptionKey"
    :icon="icon"
    :can-create="canCreate"
    :create-buttons="createButtons"
    :refreshing="pending"
    @create="emit('create')"
    @create-button="emit('createButton', $event)"
    @refresh="emit('refresh')"
  >
    <WorkspaceAppBoardShell
      v-model:collapsed="collapsed"
      v-model:mobile-open="mobileOpen"
      v-model:rail-search="railSearch"
      v-model:header-search="headerSearch"
      v-model:date-start="dateStart"
      v-model:date-end="dateEnd"
      v-model:view-mode="viewMode"
      :rail-title-key="railTitleKey"
      :rail-icon="railIcon"
      :expand-label-key="expandLabelKey"
      :collapse-label-key="collapseLabelKey"
      :rail-search-placeholder-key="railSearchPlaceholderKey"
      :header-search-placeholder-key="headerSearchPlaceholderKey"
      :pending="pending"
      :show-pending-overlay="showPendingOverlay"
      :error="error || undefined"
      @retry="emit('retry')"
    >
      <template v-if="$slots.alerts" #alerts>
        <slot name="alerts" />
      </template>

      <template v-if="$slots['rail-pills']" #rail-pills>
        <slot
          name="rail-pills"
          :rail-collapsed="railCollapsed"
          :is-small-screen="isSmallScreen"
          :close-mobile="closeMobile"
          :on-rail-select="onRailSelect"
        />
      </template>

      <template v-if="$slots['rail-items']" #rail-items>
        <slot
          name="rail-items"
          :rail-collapsed="railCollapsed"
          :is-small-screen="isSmallScreen"
          :close-mobile="closeMobile"
          :on-rail-select="onRailSelect"
        />
      </template>

      <template v-if="$slots['header-extra']" #header-extra>
        <slot name="header-extra" />
      </template>

      <slot
        :rail-collapsed="railCollapsed"
        :is-small-screen="isSmallScreen"
        :close-mobile="closeMobile"
        :on-rail-select="onRailSelect"
      />
    </WorkspaceAppBoardShell>

    <slot name="dialogs" />
  </WorkspaceAppWorkspacePage>
</template>

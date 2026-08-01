<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'
import type { RowActionItem } from '~/types/docetra/row-actions'
import { DEFAULT_ROW_ACTIONS } from '~/types/docetra/row-actions'

const props = withDefaults(defineProps<{
  row: Record<string, unknown>
  actions?: RowActionItem[]
  /** Always show the trigger (default: show on row hover). */
  alwaysVisible?: boolean
  size?: 'xs' | 'sm' | 'md'
}>(), {
  actions: () => DEFAULT_ROW_ACTIONS,
  alwaysVisible: false,
  size: 'xs',
})

const emit = defineEmits<{
  action: [payload: { key: string, row: Record<string, unknown> }]
}>()

const { t, te } = useI18n()

const visibleActions = computed(() =>
  (props.actions || []).filter(action => !action.hidden?.(props.row)),
)

const menuItems = computed<DropdownMenuItem[][]>(() => {
  const items = visibleActions.value.map((action) => {
    const label = action.label
      || (action.labelKey && te(action.labelKey) ? t(action.labelKey) : action.key)

    return {
      label,
      icon: action.icon,
      color: action.color,
      disabled: action.disabled,
      onSelect: (e: Event) => {
        e.preventDefault()
        emit('action', { key: action.key, row: props.row })
      },
    } satisfies DropdownMenuItem
  })

  return items.length ? [items] : []
})
</script>

<template>
  <UDropdownMenu
    v-if="menuItems[0]?.length"
    :items="menuItems"
    :content="{ align: 'end', side: 'bottom', sideOffset: 4 }"
  >
    <UButton
      icon="i-lucide-ellipsis"
      color="neutral"
      variant="ghost"
      :size="size"
      square
      class="shrink-0 transition"
      :class="alwaysVisible
        ? ''
        : 'opacity-70 hover:opacity-100 group-hover:opacity-100 group-focus-within:opacity-100'"
      :aria-label="$t('docetra.actions.more')"
      @click.stop
    />
  </UDropdownMenu>
</template>

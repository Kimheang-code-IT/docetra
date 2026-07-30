<script setup lang="ts">
import type { DropdownMenuItem } from '@nuxt/ui'

const props = withDefaults(defineProps<{
  canCreate?: boolean
  createLabel?: string
  createIcon?: string
  refreshing?: boolean
  moreItems?: DropdownMenuItem[][]
}>(), {
  canCreate: true,
  createIcon: 'i-lucide-plus',
  refreshing: false,
  moreItems: undefined,
})

const emit = defineEmits<{
  refresh: []
  create: []
}>()

const { t } = useI18n()
const toast = useToast()

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
</script>

<template>
  <LayoutAppHeaderActions>
    <slot name="leading" />

    <UButton
      color="neutral"
      variant="soft"
      icon="i-lucide-refresh-cw"
      square
      :loading="refreshing"
      class="rounded-md"
      :aria-label="$t('docetra.actions.refresh')"
      @click="emit('refresh')"
    />

    <UDropdownMenu :items="menuItems" :content="{ align: 'end' }">
      <UButton
        color="neutral"
        variant="soft"
        icon="i-lucide-ellipsis"
        square
        class="rounded-md"
        :aria-label="$t('common.actions')"
      />
    </UDropdownMenu>

    <UButton
      v-if="canCreate"
      color="neutral"
      variant="solid"
      :icon="createIcon"
      :label="resolvedCreateLabel"
      class="rounded-md"
      @click="emit('create')"
    />

    <slot />
  </LayoutAppHeaderActions>
</template>

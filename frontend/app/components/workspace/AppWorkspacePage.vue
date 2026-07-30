<script setup lang="ts">
import { useAppHeader } from '~/composables/layout/useAppHeader'

const props = defineProps<{
  titleKey: string
  descriptionKey?: string
  icon?: string
  canCreate?: boolean
  createLabelKey?: string
}>()

const emit = defineEmits<{
  create: []
  refresh: []
}>()

const { t } = useI18n()
const { setTitle, clear } = useAppHeader()

watch(
  () => [props.titleKey, t(props.titleKey)] as const,
  ([, label]) => setTitle(label),
  { immediate: true },
)

onBeforeUnmount(clear)

useHead(() => ({
  title: `${t(props.titleKey)} · ${t('docetra.brand.name')}`,
}))
</script>

<template>
  <div class="flex min-h-0 flex-1 flex-col overflow-hidden bg-muted/20">
    <LayoutAppHeaderPageActions
      :can-create="canCreate !== false"
      :create-label="$t(createLabelKey || 'docetra.actions.addItem')"
      @refresh="emit('refresh')"
      @create="emit('create')"
    />

    <div class="flex min-h-0 w-full min-w-0 flex-1 flex-col overflow-hidden px-1.5 pt-1.5 pb-0">
      <slot />
    </div>
  </div>
</template>

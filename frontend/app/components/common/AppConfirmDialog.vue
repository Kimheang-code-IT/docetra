<script setup lang="ts">
const open = defineModel<boolean>('open', { default: false })

const props = withDefaults(defineProps<{
  title?: string
  titleKey?: string
  description?: string
  descriptionKey?: string
  descriptionParams?: Record<string, unknown>
  confirmLabel?: string
  confirmLabelKey?: string
  cancelLabel?: string
  cancelLabelKey?: string
  confirmColor?: 'error' | 'primary' | 'neutral' | 'warning'
  loading?: boolean
  ui?: Record<string, unknown>
}>(), {
  confirmColor: 'error',
  loading: false,
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const { t, te } = useI18n()

const resolvedTitle = computed(() => {
  if (props.title) return props.title
  if (props.titleKey && te(props.titleKey)) return t(props.titleKey)
  return t('docetra.common.confirmTitle')
})
</script>

<template>
  <CommonAppDialogShell
    v-model:open="open"
    :title="resolvedTitle"
    :description="description"
    :description-key="descriptionKey"
    :description-params="descriptionParams"
    :confirm-label="confirmLabel"
    :confirm-label-key="confirmLabelKey"
    :cancel-label="cancelLabel"
    :cancel-label-key="cancelLabelKey"
    :confirm-color="confirmColor"
    :loading="loading"
    :ui="ui"
    @confirm="emit('confirm')"
    @cancel="emit('cancel')"
  >
    <slot />
  </CommonAppDialogShell>
</template>

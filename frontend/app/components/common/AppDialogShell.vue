<script setup lang="ts">
/**
 * Shared dialog chrome. Domain dialogs keep their own state and validation.
 * `card` = UModal + UCard (confirm/topic). `modal` = native UModal header/body/footer.
 */
const open = defineModel<boolean>('open', { default: false })

const props = withDefaults(defineProps<{
  title?: string
  titleKey?: string
  description?: string
  descriptionKey?: string
  descriptionParams?: Record<string, unknown>
  loading?: boolean
  dismissible?: boolean
  scrollable?: boolean
  size?: 'sm' | 'md' | 'lg' | 'fullscreen'
  variant?: 'card' | 'modal'
  confirmLabel?: string
  confirmLabelKey?: string
  cancelLabel?: string
  cancelLabelKey?: string
  confirmColor?: 'error' | 'primary' | 'neutral' | 'warning'
  canSubmit?: boolean
  hideCancel?: boolean
  hideFooter?: boolean
  confirmIcon?: string
  ui?: Record<string, unknown>
}>(), {
  loading: false,
  dismissible: true,
  scrollable: false,
  size: 'sm',
  variant: 'card',
  confirmColor: 'primary',
  canSubmit: true,
  hideCancel: false,
  hideFooter: false,
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

const { t, te } = useI18n()

const resolvedTitle = computed(() => {
  if (props.title) return props.title
  if (props.titleKey && te(props.titleKey)) return t(props.titleKey)
  return ''
})

const resolvedDescription = computed(() => {
  if (props.description) return props.description
  if (props.descriptionKey && te(props.descriptionKey)) {
    return t(props.descriptionKey, props.descriptionParams || {})
  }
  return ''
})

const resolvedConfirm = computed(() => {
  if (props.confirmLabel) return props.confirmLabel
  if (props.confirmLabelKey && te(props.confirmLabelKey)) return t(props.confirmLabelKey)
  return t('docetra.common.confirm')
})

const resolvedCancel = computed(() => {
  if (props.cancelLabel) return props.cancelLabel
  if (props.cancelLabelKey && te(props.cancelLabelKey)) return t(props.cancelLabelKey)
  return t('docetra.common.cancel')
})

const sizeUi = computed(() => {
  if (props.size === 'fullscreen') {
    return {
      content: 'bg-default flex flex-col h-dvh max-h-dvh overflow-hidden',
      header: 'shrink-0 border-b border-default px-4 py-3',
      body: 'flex-1 min-h-0 overflow-hidden p-0',
      footer: 'shrink-0 border-t border-default px-4 py-3',
    }
  }
  if (props.size === 'lg') {
    return { content: 'w-[calc(100%-2rem)] max-w-2xl sm:max-w-2xl' }
  }
  if (props.size === 'md') {
    return { content: 'w-[calc(100%-2rem)] max-w-lg sm:max-w-lg' }
  }
  return { content: 'sm:max-w-md' }
})

const mergedUi = computed(() => ({
  ...sizeUi.value,
  ...(props.ui || {}),
}))

function onCancel() {
  if (props.loading) return
  open.value = false
  emit('cancel')
}

function onConfirm() {
  if (!props.canSubmit || props.loading) return
  emit('confirm')
}
</script>

<template>
  <UModal
    v-model:open="open"
    :dismissible="dismissible && !loading"
    :scrollable="scrollable"
    :fullscreen="size === 'fullscreen'"
    :title="variant === 'modal' && !$slots.header ? (resolvedTitle || undefined) : undefined"
    :description="variant === 'modal' && !$slots.header ? (resolvedDescription || undefined) : undefined"
    :ui="mergedUi"
  >
    <template v-if="variant === 'card'" #content>
      <UCard>
        <template #header>
          <slot name="header">
            <h3 v-if="resolvedTitle" class="text-base font-semibold text-highlighted">
              {{ resolvedTitle }}
            </h3>
          </slot>
        </template>

        <p v-if="resolvedDescription && !$slots.header" class="mb-3 text-sm text-muted">
          {{ resolvedDescription }}
        </p>
        <slot />

        <template v-if="!hideFooter || $slots.footer" #footer>
          <slot name="footer">
            <div class="flex justify-end gap-2">
              <UButton
                v-if="!hideCancel"
                color="neutral"
                variant="ghost"
                :disabled="loading"
                @click="onCancel"
              >
                {{ resolvedCancel }}
              </UButton>
              <UButton
                :color="confirmColor"
                :icon="confirmIcon"
                :loading="loading"
                :disabled="!canSubmit"
                @click="onConfirm"
              >
                {{ resolvedConfirm }}
              </UButton>
            </div>
          </slot>
        </template>
      </UCard>
    </template>

    <template v-if="variant === 'modal' && $slots.header" #header>
      <slot name="header" />
    </template>

    <template v-if="variant === 'modal'" #body>
      <slot />
    </template>

    <template v-if="variant === 'modal' && (!hideFooter || $slots.footer)" #footer>
      <slot name="footer">
        <div class="flex w-full justify-end gap-2">
          <UButton
            v-if="!hideCancel"
            color="neutral"
            variant="ghost"
            :disabled="loading"
            @click="onCancel"
          >
            {{ resolvedCancel }}
          </UButton>
          <UButton
            :color="confirmColor"
            :icon="confirmIcon"
            :loading="loading"
            :disabled="!canSubmit"
            @click="onConfirm"
          >
            {{ resolvedConfirm }}
          </UButton>
        </div>
      </slot>
    </template>
  </UModal>
</template>

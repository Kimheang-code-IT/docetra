<script setup lang="ts">
/**
 * Single app-wide confirm dialog host.
 * Driven by useConfirm() — mount once in app.vue.
 * Resolution (raw text vs i18n key vs defaults) lives in CommonAppConfirmDialog.
 */
import { useConfirm } from '~/composables/common/useConfirm'

const { confirmState, accept, dismiss } = useConfirm()

const open = computed({
  get: () => confirmState.open,
  set: (value: boolean) => {
    if (!value && confirmState.open) dismiss()
  },
})
</script>

<template>
  <CommonAppConfirmDialog
    v-model:open="open"
    :title="confirmState.title"
    :title-key="confirmState.titleKey"
    :description="confirmState.description"
    :description-key="confirmState.descriptionKey"
    :description-params="confirmState.descriptionParams"
    :confirm-label="confirmState.confirmLabel"
    :confirm-label-key="confirmState.confirmLabelKey"
    :cancel-label="confirmState.cancelLabel"
    :cancel-label-key="confirmState.cancelLabelKey"
    :confirm-color="confirmState.confirmColor"
    :loading="confirmState.loading"
    :ui="{ overlay: 'z-[200]', content: 'z-[200]' }"
    @confirm="accept"
    @cancel="dismiss"
  />
</template>

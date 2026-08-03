<script setup lang="ts">
const open = defineModel<boolean>('open', { default: false })

const props = withDefaults(defineProps<{
  titleKey?: string
  descriptionKey?: string
}>(), {
  titleKey: 'docetra.common.unsavedTitle',
  descriptionKey: 'docetra.common.unsavedDescription',
})

const emit = defineEmits<{
  discard: []
  stay: []
}>()

const { t } = useI18n()

function stay() {
  open.value = false
  emit('stay')
}

function discard() {
  open.value = false
  emit('discard')
}
</script>

<template>
  <UModal v-model:open="open">
    <template #content>
      <UCard>
        <template #header>
          <h3 class="text-base font-semibold text-highlighted">
            {{ t(titleKey) }}
          </h3>
        </template>

        <p class="text-sm text-muted">
          {{ t(descriptionKey) }}
        </p>

        <template #footer>
          <div class="flex justify-end gap-2">
            <UButton color="neutral" variant="ghost" @click="stay">
              {{ t('docetra.common.keepEditing') }}
            </UButton>
            <UButton color="error" @click="discard">
              {{ t('docetra.common.discardChanges') }}
            </UButton>
          </div>
        </template>
      </UCard>
    </template>
  </UModal>
</template>

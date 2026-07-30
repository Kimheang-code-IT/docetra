<script setup lang="ts">
withDefaults(defineProps<{
  message?: string | null
  title?: string
  retryLabel?: string
}>(), {
  message: null,
  title: 'Unable to load data',
  retryLabel: 'Retry'
})

const emit = defineEmits<{
  (e: 'retry'): void
}>()
</script>

<template>
  <UAlert
    v-if="message"
    color="error"
    variant="soft"
    icon="i-lucide-triangle-alert"
    class="mb-2"
    :title="title"
    :description="message"
  >
    <template #actions>
      <UButton
        color="error"
        variant="outline"
        size="xs"
        :label="retryLabel"
        @click="emit('retry')"
      />
    </template>
  </UAlert>
</template>

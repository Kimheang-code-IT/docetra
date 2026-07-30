<script setup lang="ts">
withDefaults(defineProps<{
  loading?: boolean
}>(), {
  loading: false,
})

const emit = defineEmits<{
  reload: []
}>()
</script>

<template>
  <UButton
    icon="i-lucide-rotate-cw"
    color="neutral"
    variant="ghost"
    class="font-normal shrink-0"
    :loading="loading"
    :aria-label="$t('common.reloadData')"
    @click="emit('reload')"
  />
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  title?: string
  description?: string
  icon?: string
}>(), {
  icon: 'i-lucide-inbox',
})
</script>

<template>
  <div class="flex flex-col items-center justify-center py-14 px-4 text-center">
    <div class="size-14 rounded-full bg-muted/40 flex items-center justify-center mb-3">
      <UIcon :name="icon" class="size-7 text-muted-foreground/50" />
    </div>
    <p class="text-sm font-semibold text-highlighted">
      {{ title || $t('common.noData') }}
    </p>
    <p v-if="description" class="text-xs text-muted-foreground mt-1 max-w-sm">
      {{ description }}
    </p>
    <slot />
  </div>
</template>

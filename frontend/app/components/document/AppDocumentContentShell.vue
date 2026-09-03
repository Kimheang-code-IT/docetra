<script setup lang="ts">
/**
 * Shared readable width for document forms / comments / alerts.
 * Always uses the longest (wide) content measure so forms, comments,
 * and dense editors share one consistent column.
 */
defineProps<{
  /** Kept for call-site compatibility; width is always the longest measure. */
  wide?: boolean
}>()
</script>

<template>
  <div class="mx-auto w-full max-w-4xl px-4 sm:px-6 md:px-8 lg:max-w-5xl lg:px-10 xl:max-w-6xl xl:px-12">
    <slot />
  </div>
</template>

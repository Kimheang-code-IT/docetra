<script setup lang="ts">
withDefaults(defineProps<{
  height?: string
}>(), {
  height: '220px',
})
</script>

<template>
  <div class="w-full animate-pulse space-y-3 p-4" :style="{ minHeight: height }">
    <USkeleton class="h-4 w-1/3" />
    <USkeleton class="h-full w-full rounded-lg" :style="{ minHeight: `calc(${height} - 2rem)` }" />
  </div>
</template>

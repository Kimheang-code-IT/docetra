<script setup lang="ts">
const route = useRoute()
const id = String(route.params.id || '')
await navigateTo(id ? `/records/logs/${id}` : '/records/logs', { redirectCode: 301, replace: true })
</script>

<template>
  <div />
</template>

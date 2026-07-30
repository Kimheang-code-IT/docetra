<script setup lang="ts">
import type { EntityConfig } from '~/config/entities'

defineProps<{
  config: EntityConfig
}>()
</script>

<template>
  <DocumentAppDocumentPage :config="config" />
</template>

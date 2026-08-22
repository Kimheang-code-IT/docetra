<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('sectors')

definePageMeta({
  titleKey: 'docetra.pages.sector',
  permission: 'organizations.sectors.create',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

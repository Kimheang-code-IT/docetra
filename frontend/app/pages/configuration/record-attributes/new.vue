<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('recordAttributes')

definePageMeta({
  titleKey: 'docetra.pages.recordAttribute',
  permission: 'configuration.record_attributes.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

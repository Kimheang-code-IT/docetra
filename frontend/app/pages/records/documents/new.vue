<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('documents')

definePageMeta({
  titleKey: 'docetra.pages.document',
  permission: 'records.documents.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

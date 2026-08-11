<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('outgoingDocuments')

definePageMeta({
  titleKey: 'docetra.pages.outgoingDocument',
  permission: 'records.outgoing_documents.create',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

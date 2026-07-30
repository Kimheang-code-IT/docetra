<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('incomingDocuments')

definePageMeta({
  titleKey: 'docetra.pages.incomingDocument',
  permission: 'records.incoming_documents.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

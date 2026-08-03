<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.documentType',
  permission: 'configuration.document_types.view',
})
</script>

<template>
  <ConfigurationAppDocumentTypeEditor document-type-id="new" />
</template>

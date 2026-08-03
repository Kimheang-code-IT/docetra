<script setup lang="ts">
definePageMeta({
  titleKey: 'docetra.pages.documentType',
  permission: 'configuration.document_types.view',
})

const route = useRoute()
const id = computed(() => String(route.params.id || ''))
</script>

<template>
  <ConfigurationAppDocumentTypeEditor :document-type-id="id" />
</template>

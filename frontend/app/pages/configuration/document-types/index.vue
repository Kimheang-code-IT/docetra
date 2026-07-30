<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('documentTypes')

definePageMeta({
  titleKey: 'docetra.pages.documentType',
  permission: 'configuration.document_types.view',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>

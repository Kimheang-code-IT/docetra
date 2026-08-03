<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('recordLogs')

definePageMeta({
  titleKey: 'docetra.pages.recordLog',
  permission: 'records.logs.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

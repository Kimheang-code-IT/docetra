<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('portalLogs')

definePageMeta({
  titleKey: 'docetra.pages.portalLog',
  permission: 'portal.logs.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

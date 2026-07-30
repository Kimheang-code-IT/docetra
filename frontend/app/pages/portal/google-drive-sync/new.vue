<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('googleDriveSync')

definePageMeta({
  titleKey: 'docetra.pages.googleDriveSync',
  permission: 'portal.google_drive_sync.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

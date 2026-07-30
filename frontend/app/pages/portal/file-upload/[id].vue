<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('fileUploads')

definePageMeta({
  titleKey: 'docetra.pages.fileUpload',
  permission: 'portal.file_upload.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

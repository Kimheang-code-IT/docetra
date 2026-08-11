<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('meetingHistory')

definePageMeta({
  titleKey: 'docetra.pages.meetingHistory',
  permission: 'meetings.history.create',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

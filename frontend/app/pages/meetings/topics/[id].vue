<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('meetingTopics')

definePageMeta({
  titleKey: 'docetra.pages.meetingTopic',
  permission: 'meetings.topics.view',
})
</script>

<template>
  <DocumentEntityDocumentView :config="config" />
</template>

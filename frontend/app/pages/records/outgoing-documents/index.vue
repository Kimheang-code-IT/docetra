<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('outgoingDocuments')

definePageMeta({
  titleKey: 'docetra.pages.outgoingDocument',
  permission: 'records.outgoing_documents.view',
})
</script>

<template>
  <RecordAppRecordStageBoard
    :config="config"
    date-field="sentDate"
    subtitle-field="recipientOrganization.name"
    state-key="record-stage-outgoing"
  />
</template>

<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('incomingDocuments')

definePageMeta({
  titleKey: 'docetra.pages.incomingDocument',
  permission: 'records.incoming_documents.view',
})
</script>

<template>
  <RecordAppRecordStageBoard
    :config="config"
    date-field="receivedDate"
    subtitle-field="senderOrganization.name"
    state-key="record-stage-incoming"
  />
</template>

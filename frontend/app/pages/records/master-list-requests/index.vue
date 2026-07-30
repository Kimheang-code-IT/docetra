<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('masterListRequests')

definePageMeta({
  titleKey: 'docetra.pages.masterListRequest',
  permission: 'records.master_list_requests.view',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>

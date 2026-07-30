<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('recordTypes')

definePageMeta({
  titleKey: 'docetra.pages.recordType',
  permission: 'configuration.record_types.view',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>

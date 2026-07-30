<script setup lang="ts">
import { getEntityConfig } from '~/config/entities'

const config = getEntityConfig('systemLogs')

definePageMeta({
  titleKey: 'docetra.pages.systemLog',
  permission: 'system.logs.view',
})
</script>

<template>
  <WorkspaceEntityWorkspaceView :config="config" />
</template>
